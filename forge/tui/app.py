from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, DataTable, Footer, Input
from forge.services.telemetry import system_snapshot, top_processes
from forge.services.drift import create_baseline, check_drift
from forge.services.preflight import run_preflight
from forge.services.missions import inspect_mission, verify_diagnosis, list_missions
from forge.services.linux_lab import LinuxLab
from forge.services.webapp_mission import verify_webapp_setup


class ForgeApp(App):
    TITLE = "FORGE"

    CSS = """
    Screen {
        background: #0A0A0A;
        color: #E8E8E8;
    }

    #shell {
        height: 1fr;
        padding: 1 2;
    }

    #brand {
        height: 3;
        color: #FFFFFF;
        text-style: bold;
        content-align: left middle;
    }

    #nav {
        height: 3;
        border-bottom: solid #303030;
        color: #909090;
    }

    #heading {
        height: 4;
        padding-top: 1;
        color: #FFFFFF;
        text-style: bold;
    }

    #metrics {
        height: 10;
    }

    .metric {
        width: 1fr;
        margin-right: 1;
        background: #141414;
        border: solid #252525;
        padding: 1 2;
    }

    .metric-label {
        color: #888888;
        text-style: bold;
    }

    .metric-value {
        color: #FFFFFF;
        text-style: bold;
        padding-top: 1;
    }

    .metric-bar {
        color: #BDBDBD;
        padding-top: 1;
    }

    #details {
        height: 13;
        background: #141414;
        border: solid #252525;
        padding: 1 2;
        margin-top: 1;
    }

    #table {
        height: 1fr;
        background: #141414;
    }

    #console-scroll {
        height: 1fr;
        min-height: 5;
        background: #141414;
        border: solid #252525;
        padding: 1 2;
        overflow-y: auto;
    }

    #console {
        height: auto;
        width: 100%;
        background: #141414;
    }

    #status {
        height: 2;
        color: #888888;
        padding-top: 1;
    }

    Footer {
        background: #141414;
        color: #BDBDBD;
    }

    DataTable {
        background: #141414;
        color: #E8E8E8;
    }
    """

    BINDINGS = [
        ("1", "overview", "Overview"),
        ("2", "processes", "Processes"),
        ("3", "diagnostics", "Diagnostics"),
        ("4", "engineering", "Engineering"),
        ("5", "drift", "Drift"),
        ("6", "preflight", "Preflight"),
        ("7", "missions", "Missions"),
        ("left", "previous_mission", "Previous mission"),
        ("right", "next_mission", "Next mission"),
        ("a", "diagnose_a", "Diagnosis A"),
        ("b", "diagnose_b", "Diagnosis B"),
        ("c", "diagnose_c", "Diagnosis C"),
        ("p", "run_preflight", "Run preflight"),
        ("ctrl+b", "baseline", "Set baseline"),
        ("ctrl+c", "check_drift", "Check drift"),
        ("r", "refresh", "Refresh"),
        ("escape", "toggle_lab_focus", "Terminal focus"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="shell"):
            yield Static(
                "F O R G E   /   LINUX ENGINEERING WORKSTATION",
                id="brand",
            )

            yield Static(
                "01  OVERVIEW     02  PROCESSES     "
                "03  DIAGNOSTICS     04  ENGINEERING     05  DRIFT     06  PREFLIGHT",
                id="nav",
            )

            yield Static("SYSTEM OVERVIEW", id="heading")

            with Horizontal(id="metrics"):
                for key, label in (
                    ("cpu", "CPU LOAD"),
                    ("memory", "MEMORY"),
                    ("disk", "STORAGE"),
                ):
                    with Vertical(classes="metric"):
                        yield Static(label, classes="metric-label")
                        yield Static("—", id=f"{key}-value", classes="metric-value")
                        yield Static("░" * 20, id=f"{key}-bar", classes="metric-bar")

            yield Static("Loading node profile...", id="details")

            yield DataTable(id="table")

            with VerticalScroll(id="console-scroll"):
                yield Static("", id="console")
            yield Input(
                placeholder="Enter a Linux command, then press Enter...",
                id="lab-input",
            )

            yield Static("LOCAL NODE  /  READ-ONLY MODE", id="status")

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.add_columns("PID", "PROCESS", "CPU %", "MEM %")
        table.cursor_type = "row"

        self.linux_lab = LinuxLab()
        self._lab_history = []
        from forge.services.webapp_persistence import load_webapp_evidence

        try:
            self._lab_commands = load_webapp_evidence(self.linux_lab)
        except (OSError, ValueError, TypeError):
            self._lab_commands = []
        self.current_workspace = "overview"
        self.show_workspace("overview")
        self.refresh_data()
        self.set_interval(5, self.refresh_data)

    def show_workspace(self, name: str) -> None:
        self.current_workspace = name

        # Hidden tables must not retain keyboard focus.
        if name == "processes":
            self.set_focus(self.query_one("#table", DataTable))
        elif name == "engineering":
            self.set_focus(self.query_one("#lab-input", Input))
        else:
            self.set_focus(None)

        titles = {
            "overview": "SYSTEM OVERVIEW",
            "processes": "PROCESS INSPECTION",
            "diagnostics": "SYSTEM DIAGNOSTICS",
            "engineering": "ENGINEERING WORKSPACE",
            "drift": "CONFIGURATION DRIFT",
            "preflight": "DEPLOYMENT PREFLIGHT",
            "missions": "ENGINEERING MISSIONS",
        }

        self.query_one("#heading", Static).update(titles[name])

        self.query_one("#metrics").display = name == "overview"
        self.query_one("#details").display = name in ("overview", "diagnostics")
        self.query_one("#table").display = name == "processes"
        self.query_one("#console-scroll").display = name in ("diagnostics", "engineering", "drift", "preflight", "missions")
        self.query_one("#lab-input", Input).display = name == "engineering"

        self.query_one("#nav", Static).update(
            "     ".join(
                f"[bold white]{i:02d}  {label}[/]"
                if key == name
                else f"[#777777]{i:02d}  {label}[/]"
                for i, (key, label) in enumerate(
                    (
                        ("overview", "OVERVIEW"),
                        ("processes", "PROCESSES"),
                        ("diagnostics", "DIAGNOSTICS"),
                        ("engineering", "ENGINEERING"),
                        ("drift", "DRIFT"),
                        ("preflight", "PREFLIGHT"),
                        ("missions", "MISSIONS"),
                    ),
                    start=1,
                )
            )
        )

        if name == "missions":
            self.render_mission()

        if name == "drift":
            self.render_drift()
        elif name == "preflight":
            self.render_preflight()

        if name == "engineering":
            self.render_linux_lab()

        self.query_one("#status", Static).update(
            f"FORGE  /  {name.upper()}   •   R REFRESH   •   Q EXIT"
        )

    def refresh_data(self) -> None:
        try:
            data = system_snapshot()

            for key in ("cpu", "memory", "disk"):
                value = float(data[key]["usage_percent"])
                self.query_one(f"#{key}-value", Static).update(
                    f"{value:.1f}%"
                )

                filled = max(0, min(20, round(value / 5)))
                self.query_one(f"#{key}-bar", Static).update(
                    "━" * filled + "─" * (20 - filled)
                )

            self.query_one("#details", Static).update(
                "[bold white]NODE PROFILE[/]\n\n"
                f"  HOSTNAME       {data['hostname']}\n"
                f"  PLATFORM       {data['platform']}\n"
                f"  KERNEL         {data['kernel']}\n"
                f"  CPU CORES      {data['cpu']['logical_cores']}\n"
                f"  PROCESSES      {data['process_count']}\n"
                f"  UPTIME         {data['uptime_seconds'] // 3600} hours"
            )

            table = self.query_one("#table", DataTable)
            table.clear()

            for proc in top_processes():
                table.add_row(
                    str(proc["pid"]),
                    str(proc["name"]),
                    f"{proc['cpu_percent']:.1f}",
                    f"{proc['memory_percent']:.2f}",
                )

            if self.current_workspace == "diagnostics":
                self.show_diagnostics(data)

        except Exception as exc:
            self.query_one("#status", Static).update(
                f"ERROR: {type(exc).__name__}: {exc}"
            )

    def show_diagnostics(self, data):
        findings = []

        for key in ("cpu", "memory", "disk"):
            value = data[key]["usage_percent"]

            if value >= 90:
                findings.append(f"CRITICAL  {key.upper()}  {value:.1f}%")
            elif value >= 75:
                findings.append(f"WARNING   {key.upper()}  {value:.1f}%")

        if not findings:
            findings = ["No resource threshold warnings detected."]

        self.query_one("#console", Static).update(
            "[bold white]DIAGNOSTIC RESULTS[/]\n\n"
            + "\n\n".join(findings)
            + "\n\n[#777777]Warning ≥75%  /  Critical ≥90%[/]"
        )


    def render_drift(self):
        try:
            result = check_drift()
            status = result["status"]

            if status == "no_baseline":
                message = (
                    "NO BASELINE EXISTS\\n\\n"
                    "Press B to establish the current configuration "
                    "as the approved baseline."
                )
            elif status == "clean":
                message = (
                    "CLEAN / NO CONFIGURATION DRIFT\\n\\n"
                    f"Verified {result['checked_files']} tracked files."
                )
            else:
                lines = [
                    f"{item['state']:10} {item['file']}"
                    for item in result["changes"]
                ]
                message = (
                    "CONFIGURATION CHANGES DETECTED\\n\\n"
                    + "\\n".join(lines)
                )

            self.query_one("#console", Static).update(
                "[bold white]CONFIGURATION INTEGRITY[/]\\n\\n"
                + message
                + "\\n\\n[#888888]"
                  "B  CREATE BASELINE    C  CHECK DRIFT"
                  "[/]"
            )

        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.query_one("#console", Static).update(
                f"DRIFT CHECK FAILED: {type(exc).__name__}: {exc}"
            )

    def action_drift(self):
        self.show_workspace("drift")

    def action_check_drift(self):
        if self.current_workspace == "drift":
            self.render_drift()

    def action_baseline(self):
        if self.current_workspace != "drift":
            return

        try:
            create_baseline()
            self.render_drift()
            self.notify("Configuration baseline saved.")
        except (OSError, ValueError) as exc:
            self.notify(
                f"Baseline failed: {exc}",
                severity="error",
            )


    def render_preflight(self):
        try:
            report = run_preflight()

            lines = [
                f"[bold white]DEPLOYMENT PREFLIGHT / {report['overall']}[/]",
                "",
            ]

            for check in report["checks"]:
                status = check["status"]
                color = {
                    "PASS": "#BDBDBD",
                    "WARN": "#E3BD79",
                    "FAIL": "#F18B8B",
                }[status]

                lines.append(
                    f"[{color}]{status:<5}[/] "
                    f"{check['name']:<25} {check['detail']}"
                )

            lines.extend([
                "",
                f"Checks completed: {report['checked']}",
                "",
                "[#888888]P  RERUN PREFLIGHT[/]",
            ])

            self.query_one("#console", Static).update(
                "\\n".join(lines)
            )

        except Exception as exc:
            self.query_one("#console", Static).update(
                f"PREFLIGHT ERROR: {type(exc).__name__}: {exc}"
            )

    def action_preflight(self):
        self.show_workspace("preflight")

    def action_run_preflight(self):
        if self.current_workspace == "preflight":
            self.render_preflight()



    def render_mission(self, answer=None):
        catalog = list_missions()

        if not hasattr(self, "_mission_index"):
            self._mission_index = 0

        self._mission_index %= len(catalog)
        selected = catalog[self._mission_index]
        mission = inspect_mission(selected["id"])

        lines = [
            "[bold white]ENGINEERING MISSIONS[/]",
            "[#888888]SIMULATED LINUX INCIDENT LAB[/]",
            "",
            (
                f"MISSION {self._mission_index + 1:02} / "
                f"{len(catalog):02}     "
                f"{mission['title'].upper()}"
            ),
            "",
            "[bold white]SCENARIO[/]",
            mission["scenario"],
            "",
            "[bold white]DIAGNOSTIC EVIDENCE[/]",
        ]

        for index, evidence in enumerate(
            mission["evidence"], 1
        ):
            lines.append(f" {index:02}  {evidence}")

        lines.extend([
            "",
            "[bold white]ROOT-CAUSE ANALYSIS[/]",
            mission["question"],
            "",
            "[#888888]"
            "A / B / C  SUBMIT DIAGNOSIS"
            "     LEFT / RIGHT  CHANGE MISSION"
            "[/]",
        ])

        if answer is not None:
            result = verify_diagnosis(
                selected["id"], answer
            )

            color = (
                "#BDBDBD"
                if result["verified"]
                else "#F18B8B"
            )

            lines.extend([
                "",
                f"[{color}]"
                f"VERIFICATION / {result['status']}"
                "[/]",
                result["explanation"],
            ])

        self.query_one("#console", Static).update(
            "\n".join(lines)
        )

    def action_next_mission(self):
        if self.current_workspace != "missions":
            return

        catalog = list_missions()
        self._mission_index = (
            getattr(self, "_mission_index", 0) + 1
        ) % len(catalog)

        self.render_mission()

    def action_previous_mission(self):
        if self.current_workspace != "missions":
            return

        catalog = list_missions()
        self._mission_index = (
            getattr(self, "_mission_index", 0) - 1
        ) % len(catalog)

        self.render_mission()

    def action_missions(self):
        self.show_workspace("missions")

    def submit_diagnosis(self, answer):
        if self.current_workspace == "missions":
            self.render_mission(answer)

    def action_diagnose_a(self):
        self.submit_diagnosis("A")

    def action_diagnose_b(self):
        if self.current_workspace == "drift":
            self.action_baseline()
        else:
            self.submit_diagnosis("B")

    def action_diagnose_c(self):
        if self.current_workspace == "drift":
            self.action_check_drift()
        else:
            self.submit_diagnosis("C")

    def action_overview(self):
        self.show_workspace("overview")

    def action_processes(self):
        self.show_workspace("processes")

    def action_diagnostics(self):
        self.show_workspace("diagnostics")
        self.show_diagnostics(system_snapshot())

    def action_engineering(self):
        self.show_workspace("engineering")

    def action_refresh(self):
        self.refresh_data()

    def action_toggle_lab_focus(self):
        """Toggle command-entry focus in Engineering."""
        if self.current_workspace != "engineering":
            return

        field = self.query_one("#lab-input", Input)

        if self.focused is field:
            self.set_focus(None)
        else:
            self.set_focus(field)

    def render_webapp_progress(self):
        """Display verified DecodeLabs practical mission progress."""
        report = verify_webapp_setup(
            self.linux_lab,
            self._lab_commands,
        )

        lines = [
            "[bold white]PRACTICAL MISSION / WEB APP SETUP[/]",
            (
                f"[bold white]PROGRESS[/]  "
                f"{report['completed']}/{report['total']}  "
                f"({report['percentage']}%)"
            ),
            "",
        ]

        for index, step in enumerate(report["steps"], 1):
            indicator = (
                "[green]PASS[/]"
                if step["passed"]
                else "[#777777]PENDING[/]"
            )

            lines.append(
                f"  {index:02d}  {indicator}  {step['title']}"
            )
            lines.append(
                f"      [#888888]{step['command']}[/]"
            )

        if report["verified"]:
            lines.extend([
                "",
                "[bold green]MISSION VERIFIED / ALL SIX STEPS COMPLETE[/]",
            ])

        return lines

    def render_linux_lab(self):
        """Show recent command output before the mission checklist."""
        lab = self.linux_lab
        history = self._lab_history[-8:]

        lines = [
            "[bold white]LINUX COMMAND TERMINAL[/]",
            f"[#888888]CURRENT DIRECTORY[/]  {lab._display(lab.cwd)}",
            "",
            "[bold white]RECENT COMMANDS / OUTPUT[/]",
        ]

        if history:
            lines.extend(history)
        else:
            lines.append(
                "[#888888]Ready. Enter pwd, ls, or mkdir below.[/]"
            )

        lines.extend([
            "",
            "[#888888]ESC: release input  |  1-7: navigate[/]",
            "",
        ])

        lines.extend(self.render_webapp_progress())

        self.query_one("#console", Static).update(
            "\n".join(lines)
        )

    def on_input_submitted(self, event: Input.Submitted):
        """Execute training commands without invoking a system shell."""
        if event.input.id != "lab-input":
            return

        command = event.value.strip()
        event.input.value = ""

        if self.current_workspace != "engineering" or not command:
            return

        if command == "clear":
            self._lab_history.clear()
        else:
            result = self.linux_lab.execute(command)
            if (
                not result.startswith("ERROR:")
                and not result.startswith("Command not supported:")
            ):
                self._lab_commands.append(command)

                from forge.services.webapp_persistence import (
                    ALLOWED_COMMANDS,
                    save_webapp_evidence,
                )

                if command in ALLOWED_COMMANDS:
                    try:
                        save_webapp_evidence(
                            self.linux_lab,
                            self._lab_commands,
                        )
                    except (OSError, ValueError, TypeError):
                        pass
            self._lab_history.append(
                f"[bold white]$[/] {command}"
            )
            if result:
                self._lab_history.append(
                    result.replace("[", "\\[")
                )

        self.render_linux_lab()


if __name__ == "__main__":
    ForgeApp().run()
