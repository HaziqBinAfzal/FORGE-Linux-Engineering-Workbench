"""Safe Linux fundamentals training workspace.

Commands operate only inside runtime/linux-lab.
No shell execution, sudo, or unrestricted filesystem access.
"""

import shlex
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = ROOT / "runtime" / "linux-lab"


class LabError(Exception):
    pass


class LinuxLab:
    def __init__(self, root=None):
        self.root = Path(root or LAB_ROOT).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.cwd = self.root
        self._pending_removal = None

    def _path(self, value="."):
        candidate = Path(value)
        if candidate.is_absolute():
            candidate = self.root / str(candidate).lstrip("/")
        else:
            candidate = self.cwd / candidate

        resolved = candidate.resolve(strict=False)

        if not resolved.is_relative_to(self.root):
            raise LabError("Access denied: outside training workspace")

        return resolved

    def _display(self, path):
        relative = path.relative_to(self.root)
        return "/" if relative == Path(".") else "/" + relative.as_posix()


    def _execute_extended(self, args):
        """Handle assignment-specific commands without a shell."""
        cmd, *params = args

        if cmd == "echo":
            if ">" not in params:
                return " ".join(params)

            if params.count(">") != 1:
                raise LabError("Usage: echo TEXT > FILE")

            index = params.index(">")

            if index == 0 or index != len(params) - 2:
                raise LabError("Usage: echo TEXT > FILE")

            destination = self._path(params[-1])

            if not destination.parent.is_dir():
                raise LabError("Parent directory does not exist")

            if destination.exists() and not destination.is_file():
                raise LabError("Destination is not a regular file")

            destination.write_text(
                " ".join(params[:index]) + "\n"
            )
            return "Text written"

        if cmd == "ls":
            recursive = "-R" in params
            detailed = "-l" in params
            names = [
                item for item in params
                if item not in ("-R", "-l")
            ]

            if any(item.startswith("-") for item in names):
                raise LabError("Unsupported ls option")

            target = self._path(names[0] if names else ".")

            if target.is_file():
                entries = [target]
            elif target.is_dir():
                if recursive:
                    entries = sorted(
                        target.rglob("*"),
                        key=lambda p: str(p)
                    )
                else:
                    entries = sorted(
                        target.iterdir(),
                        key=lambda p: p.name
                    )
            else:
                raise LabError("Path not found")

            output = []

            for entry in entries:
                relative = self._display(entry)

                if detailed:
                    import stat
                    mode = stat.filemode(entry.stat().st_mode)
                    output.append(
                        f"{mode} {entry.stat().st_size:>8} {relative}"
                    )
                else:
                    output.append(relative)

            return "\n".join(output)

        return None

    def execute(self, command):
        # Support the assignment's AND operator without using a shell.
        # Only execute the next command if the previous one succeeds.
        try:
            lexer = shlex.shlex(command, posix=True, punctuation_chars="&")
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError as exc:
            return f"ERROR: {exc}"

        if "&&" in tokens or "&" in tokens:
            if "&" in tokens or tokens[0] == "&&" or tokens[-1] == "&&":
                return "ERROR: Invalid command chaining"

            segments = []
            current = []

            for token in tokens:
                if token == "&&":
                    if not current:
                        return "ERROR: Empty chained command"
                    segments.append(current)
                    current = []
                else:
                    current.append(token)

            if not current:
                return "ERROR: Empty chained command"

            segments.append(current)

            if len(segments) > 8:
                return "ERROR: Maximum 8 chained commands"

            outputs = []

            for segment in segments:
                # shlex.join preserves quoted arguments.
                result = self.execute(shlex.join(segment))
                outputs.append(result)

                if result.startswith("ERROR:") or result.startswith(
                    "Command not supported:"
                ):
                    break

            return "\n".join(
                output for output in outputs if output
            )

        try:
            args = shlex.split(command)
        except ValueError as exc:
            return f"ERROR: {exc}"

        if not args:
            return ""

        cmd, *params = args

        try:
            from forge.services.linux_commands import execute_additional

            additional = execute_additional(self, args)
            if additional is not None:
                return additional
            if cmd == "echo" or (
                cmd == "ls"
                and any(p in ("-R", "-l") for p in params)
            ):
                return self._execute_extended(args)
            if cmd == "pwd":
                return self._display(self.cwd)

            if cmd == "ls":
                target = self._path(params[0] if params else ".")
                if target.is_file():
                    return target.name
                return "\n".join(sorted(p.name for p in target.iterdir()))

            if cmd == "cd":
                target = self._path(params[0] if params else "/")
                if not target.is_dir():
                    raise LabError("Not a directory")
                self.cwd = target
                return self._display(self.cwd)

            if cmd == "mkdir":
                parents = "-p" in params
                names = [p for p in params if p != "-p"]
                if not names:
                    raise LabError("Missing directory name")
                for name in names:
                    self._path(name).mkdir(
                        parents=parents,
                        exist_ok=parents,
                    )
                return "Directory created"

            if cmd == "touch":
                if not params:
                    raise LabError("Missing filename")
                for name in params:
                    self._path(name).touch()
                return "File created"

            if cmd == "cat":
                if not params:
                    raise LabError("Missing filename")
                return "\n".join(
                    self._path(name).read_text()
                    for name in params
                )

            if cmd == "cp":
                if len(params) != 2:
                    raise LabError("Usage: cp SOURCE DEST")
                source = self._path(params[0])
                dest = self._path(params[1])
                if not source.is_file():
                    raise LabError("Source must be a file")
                shutil.copy2(source, dest)
                return "File copied"

            if cmd == "mv":
                if len(params) != 2:
                    raise LabError("Usage: mv SOURCE DEST")
                source = self._path(params[0])
                dest = self._path(params[1])
                source.rename(dest)
                return "File moved"

            if cmd in ("yes", "no"):
                if params:
                    raise LabError("Confirmation takes no arguments")
                pending = self._pending_removal
                self._pending_removal = None
                if pending is None:
                    return "ERROR: No deletion awaiting confirmation"
                if cmd == "no":
                    return "Deletion cancelled"
                target = self._path(self._display(pending))
                if not target.is_file():
                    raise LabError("File no longer exists")
                target.unlink()
                return "File removed after confirmation"

            if cmd == "rm":
                self._pending_removal = None
                if not params:
                    raise LabError("Missing filename")
                if params[0] == "-i":
                    if len(params) != 2:
                        raise LabError("Usage: rm -i FILE")
                    target = self._path(params[1])
                    if not target.is_file():
                        raise LabError("Only regular files can be removed")
                    self._pending_removal = target
                    return (
                        f"Remove {self._display(target)}? "
                        "Type yes to confirm or no to cancel"
                    )
                if any(p.startswith("-") for p in params):
                    raise LabError(
                        "Deletion flags are disabled in this training lab"
                    )
                for name in params:
                    target = self._path(name)
                    if not target.is_file():
                        raise LabError(
                            "Only regular files can be removed"
                        )
                    target.unlink()
                return "File removed"

            return f"Command not supported: {cmd}"

        except (OSError, ValueError, LabError) as exc:
            return f"ERROR: {exc}"
