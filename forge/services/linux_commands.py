"""Additional safe Linux training commands."""

import os
import stat


def execute_additional(lab, args):
    """Return command output or None for commands handled elsewhere."""
    command, *params = args

    if command == "whoami":
        if params:
            return "ERROR: whoami takes no arguments"
        return "forge"

    if command == "id":
        if params:
            return "ERROR: id takes no arguments"
        return "uid=1000(forge) gid=1000(forge) groups=1000(forge)"

    if command == "chown":
        if len(params) != 2:
            return "ERROR: Usage: chown USER FILE"

        owner, filename = params

        if not owner or not owner.replace("_", "").isalnum():
            return "ERROR: Invalid simulated owner"

        try:
            target = lab._path(filename)
            if not target.is_file():
                return "ERROR: File not found"
        except (OSError, ValueError) as exc:
            return f"ERROR: {exc}"

        if not hasattr(lab, "_simulated_owners"):
            lab._simulated_owners = {}

        lab._simulated_owners[str(target)] = owner

        return (
            f"[Training simulation] Owner of "
            f"{lab._display(target)} set to {owner}. "
            "Actual filesystem ownership was not changed."
        )

    if command == "ssh":
        if len(params) != 1 or "@" not in params[0]:
            return "ERROR: Usage: ssh USER@HOST"

        user, host = params[0].split("@", 1)

        if not user or not host:
            return "ERROR: Usage: ssh USER@HOST"

        return (
            f"[Training simulation] ssh {user}@{host} "
            "would establish an encrypted remote login. "
            "Authentication and host verification are required. "
            "No network connection was made."
        )

    if command == "chmod":
        if len(params) != 2:
            return "ERROR: Usage: chmod MODE FILE"

        mode, filename = params

        if len(mode) not in (3, 4) or any(
            digit not in "01234567" for digit in mode
        ):
            return "ERROR: Use an octal permission mode, e.g. 754"

        if len(mode) == 4 and mode[0] != "0":
            return "ERROR: Special permission bits are not supported"

        try:
            path = lab._path(filename)
            if not path.is_file():
                return "ERROR: File not found"

            os.chmod(path, int(mode, 8))
            return f"Permissions changed to {mode}"

        except (OSError, ValueError) as exc:
            return f"ERROR: {exc}"

    if command in ("head", "tail", "less"):
        count = 10
        follow_demo = False

        if command == "less":
            if len(params) != 1:
                return "ERROR: Usage: less FILE"
            filename = params[0]

        elif command == "tail" and len(params) == 2 and params[0] == "-f":
            filename = params[1]
            follow_demo = True

        elif len(params) == 1:
            filename = params[0]

        elif (
            len(params) == 3
            and params[0] == "-n"
            and params[1].isdigit()
        ):
            count = int(params[1])
            if count > 1000:
                return "ERROR: Maximum 1000 lines"
            filename = params[2]

        else:
            return f"ERROR: Usage: {command} [-n COUNT] FILE"

        try:
            path = lab._path(filename)

            if not path.is_file():
                return "ERROR: File not found"

            if path.stat().st_size > 1_000_000:
                return "ERROR: File exceeds the 1 MB lab limit"

            lines = path.read_text().splitlines()

            if command == "head":
                selected = lines[:count]
            elif command == "tail":
                selected = lines[-count:] if count else []
            else:
                selected = lines[:100]

            output = "\n".join(selected)
            if follow_demo:
                output += (
                    "\n[Training simulation] tail -f follows new log "
                    "entries continuously on real Linux. "
                    "Press Ctrl+C to stop it."
                )
            return output

        except (OSError, UnicodeError, ValueError) as exc:
            return f"ERROR: {exc}"

    if command == "ls":
        flags = set()
        paths = []

        for item in params:
            if item.startswith("-"):
                if not item[1:] or not set(item[1:]).issubset(
                    {"a", "l", "R"}
                ):
                    return "ERROR: Unsupported ls option"
                flags.update(item[1:])
            else:
                paths.append(item)

        if len(paths) > 1:
            return "ERROR: ls accepts one path in this lab"

        try:
            target = lab._path(paths[0] if paths else ".")

            if target.is_file():
                entries = [target]
            elif target.is_dir():
                entries = sorted(
                    target.rglob("*") if "R" in flags
                    else target.iterdir(),
                    key=lambda item: str(item)
                )

                if "a" in flags and "R" not in flags:
                    entries = [target / ".", target / ".."] + entries
            else:
                return "ERROR: Path not found"

            output = []

            for entry in entries:
                if entry.name.startswith(".") and "a" not in flags:
                    continue

                if "l" in flags:
                    details = entry.stat()
                    output.append(
                        f"{stat.filemode(details.st_mode)} "
                        f"{details.st_size:>8} "
                        f"{lab._display(entry)}"
                    )
                else:
                    if "a" in flags and entry == target / ".":
                        output.append(".")
                    elif "a" in flags and entry == target / "..":
                        output.append("..")
                    else:
                        output.append(lab._display(entry))

            return "\n".join(output)

        except (OSError, ValueError) as exc:
            return f"ERROR: {exc}"

    return None
