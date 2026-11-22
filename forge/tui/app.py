from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, DataTable, Footer, Input
from forge.services.telemetry import system_snapshot, top_processes
from forge.services.live_monitor import LiveMonitor, sparkline
from forge.services.drift import create_baseline, check_drift
from forge.services.preflight import run_preflight
from forge.services.missions import inspect_mission, verify_diagnosis, list_missions
from forge.services.linux_lab import LinuxLab
from forge.services.webapp_mission import verify_webapp_setup


class ForgeApp(App):
    TITLE = "FORGE"

    CSS = """
    Screen { background: #000000; color: #E8E8E8; }
    #shell { height: 1fr; padding: 1 2; background: #000000; }
    #brand { height: 3; padding: 1 1 0 1; color: #FAFAFA; text-style: bold; }
    #nav { height: 3; padding: 0 1; color: #929292; border-bottom: solid #252525; }
    #heading { height: 3; padding: 1 1 0 1; color: #F4F4F4; text-style: bold; }
    #health { height: 2; padding: 0 1; color: #A4B4A8; background: #000000; }
    #metrics { height: 7; margin-top: 1; }
    .metric { width: 1fr; height: 6; padding: 1 2; margin-right: 1; background: #0C0C0C; }
    .metric-label { height: 1; color: #969696; text-style: bold; }
    .metric-value { height: 2; color: #FAFAFA; text-style: bold; }
    .metric-bar { height: 1; color: #A9BCAD; }
    #overview-body { height: 19; min-height: 12; margin-top: 1; }
    #details { width: 1fr; height: 100%; padding: 1 2; margin-right: 1; background: #0A0A0A; }
    #live-feed { width: 1fr; height: 100%; padding: 1 2; background: #0A0A0A; }
    #ticker { height: 2; padding: 0 1; background: #000000; color: #929292; }
    #table { height: 1fr; background: #080808; }
    #console-scroll { height: 1fr; min-height: 5; background: #080808; border: none; padding: 1 2; overflow-y: auto; }
    #console { height: auto; width: 100%; background: #080808; }
    #lab-input { border: none; border-bottom: solid #494949; background: #101010; color: #E7E7E7; }
    #lab-input:focus { border-bottom: solid #B5C7B9; }
    #status { height: 2; padding: 0 1; color: #828282; }
    Footer { display: none; }
    DataTable { background: #080808; color: #E0E0E0; }
    DataTable > .datatable--header { background: #101010; color: #D0D0D0; }
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
            yield Static("F O R G E     /     L I N U X   W O R K B E N C H", id="brand")
            yield Static("", id="nav")
            yield Static("OVERVIEW   /   SYSTEM STATUS", id="heading")
            yield Static("INITIALIZING MONITORING STREAM", id="health")
            with Horizontal(id="metrics"):
                for key, label in (
                    ("cpu", "CPU"),
                    ("memory", "MEMORY"),
                    ("disk", "DISK"),
                    ("network", "NETWORK"),
                ):
                    with Vertical(classes="metric"):
                        yield Static(label, classes="metric-label")
                        yield Static("—", id=f"{key}-value", classes="metric-value")
                        yield Static("", id=f"{key}-bar", classes="metric-bar")
            with Horizontal(id="overview-body"):
                yield Static("Collecting host information...", id="details")
                yield Static("Waiting for telemetry...", id="live-feed")
            yield Static("MONITORING STARTING", id="ticker")
            yield DataTable(id="table")
            with VerticalScroll(id="console-scroll"):
                yield Static("", id="console")
            yield Input(
                placeholder="Linux lab  /  enter command...",
                id="lab-input",
            )
            yield Static("READ ONLY  /  LIVE HOST OBSERVATION  /  ISOLATED COMMAND LAB", id="status")
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
        self._live_monitor = LiveMonitor()
        self.refresh_data()
        self.set_interval(1.5, self.refresh_data)

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
            "overview": "OVERVIEW  /  LIVE SYSTEM STATUS",
            "processes": "PROCESS INSPECTION",
            "diagnostics": "DIAGNOSTICS  /  NEXT ACTIONS",
            "engineering": "LINUX COMMAND WORKSPACE",
            "drift": "CONFIGURATION DRIFT",
            "preflight": "READINESS  /  PREFLIGHT",
            "missions": "INCIDENT PRACTICE",
        }

        self.query_one("#heading", Static).update(titles[name])

        self.query_one("#metrics").display = name == "overview"
        self.query_one("#health").display = name == "overview"
        self.query_one("#overview-body").display = name == "overview"
        self.query_one("#ticker").display = name == "overview"
        self.query_one("#details").display = name in ("overview", "diagnostics")
        self.query_one("#table").display = name == "processes"
        self.query_one("#console-scroll").display = name in ("diagnostics", "engineering", "drift", "preflight", "missions")
        self.query_one("#lab-input", Input).display = name == "engineering"

        self.query_one("#nav", Static).update(
            "    ".join(
                f"[bold white]{i}  {label}[/]" if key == name
                else f"[#858585]{i}  {label}[/]"
                for i, (key, label) in enumerate((
                    ("overview", "OVERVIEW"),
                    ("processes", "PROCESSES"),
                    ("diagnostics", "DIAGNOSTICS"),
                    ("engineering", "ENGINEERING"),
                ), 1)
            ) + "     [#666666]5-7  MORE[/]"
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
            f"{name.upper()}  /  R REFRESH  /  5 DRIFT  6 PREFLIGHT  7 INCIDENTS  /  Q EXIT"
        )

    def refresh_data(self) -> None:
        try:
            data = system_snapshot()
            assessment = self._live_monitor.update(data)
            for key in ("cpu", "memory", "disk"):
                value = float(data[key]["usage_percent"])
                self.query_one(f"#{key}-value", Static).update(f"{value:.1f}%")
                self.query_one(f"#{key}-bar", Static).update(
                    sparkline(self._live_monitor.samples[key], width=20)
                )
            self.query_one("#network-value", Static).update(
                "RX " + self._live_monitor.rate(self._live_monitor.rx_rate)
            )
            self.query_one("#network-bar", Static).update(
                "TX " + self._live_monitor.rate(self._live_monitor.tx_rate)
            )
            state = assessment["health"]
            state_color = "#D98E76" if state == "CRITICAL" else "#E0C17D" if state == "ATTENTION" else "#80C6A0"
            timestamp = str(data.get("timestamp", ""))[:19].replace("T", "  ") + " UTC"
            self.query_one("#health", Static).update(
                f"[{state_color}]●  {state}[/]     /     HOST TELEMETRY     /     "
                f"{timestamp}     /     1.5s sampling"
            )
            self.query_one("#details", Static).update(
                "[bold]NODE / ENVIRONMENT[/]\n\n"
                f"HOST             {data['hostname']}\n"
                f"KERNEL           {data['kernel']}\n"
                f"PLATFORM         {data['platform']}\n"
                f"LOGICAL CORES    {data['cpu']['logical_cores']}\n"
                f"PROCESSES        {data['process_count']}\n"
                f"UPTIME           {data['uptime_seconds'] // 3600}h {(data['uptime_seconds'] % 3600) // 60}m\n"
                f"MEM AVAILABLE    {data['memory']['available_bytes'] / (1024**3):.2f} GiB\n"
                f"DISK FREE        {data['disk']['free_bytes'] / (1024**3):.2f} GiB"
            )
            processes = top_processes()
            feed = ["[bold]SYSTEM OBSERVATIONS[/]", ""]
            if assessment["findings"]:
                for finding in assessment["findings"]:
                    feed.append(f"{finding['severity']}  {finding['name']}  /  {finding['usage']:.1f}%")
                    feed.append(f"  {finding['action']}")
                    feed.append("")
            else:
                feed.extend(["[#A8C0AF]●  System resources within thresholds[/]", "CPU / MEMORY / DISK below 75%", ""])
            feed.extend(["[bold]TOP MEMORY CONSUMERS[/]", ""])
            for proc in processes[:4]:
                feed.append(f"{str(proc['pid']):>6}  {str(proc['name'])[:19]:<19} {proc['memory_percent']:>5.1f}%")
            feed.extend(["", "Investigate: 3  /  Command lab: 4"])
            self.query_one("#live-feed", Static).update("\n".join(feed))
            self.query_one("#ticker", Static).update(
                "[bold]LIVE ACTIVITY[/]     "
                f"{len(processes)} top processes sampled    ·    "
                f"RX {self._live_monitor.rate(self._live_monitor.rx_rate)}    ·    "
                f"TX {self._live_monitor.rate(self._live_monitor.tx_rate)}    ·    "
                f"{len(assessment['findings'])} resource alerts"
            )
            table = self.query_one("#table", DataTable)
            table.clear()
            for proc in processes:
                table.add_row(str(proc["pid"]), str(proc["name"]),
                              f"{proc['cpu_percent']:.1f}", f"{proc['memory_percent']:.2f}")
            if self.current_workspace == "diagnostics":
                self.show_diagnostics(data)
        except Exception as exc:
            self.query_one("#status", Static).update(
                f"MONITORING ERROR: {type(exc).__name__}: {exc}"
            )

    def show_diagnostics(self, data):
        """Present observed resource pressure with investigation and verification steps."""
        playbooks = {
            "cpu": (
                "Sustained CPU contention may delay work. A single sample does not prove a fault.",
                "top  /  ps aux --sort=-%cpu | head",
                "Inspect the highest CPU consumers and validate workload expectations.",
                "Recheck CPU usage over several refreshes after any operator action.",
            ),
            "memory": (
                "Low available memory can affect responsiveness and cause swapping.",
                "free -h  /  ps aux --sort=-%mem | head",
                "Review memory-heavy processes and application logs before intervening.",
                "Recheck available memory and process consumption.",
            ),
            "disk": (
                "Low free disk capacity can disrupt writes, logs and applications.",
                "df -h  /  du -sh /var/log/*",
                "Identify growth and review candidates; do not delete files automatically.",
                "Recheck disk space after a separately approved cleanup.",
            ),
        }
        lines = [
            "[bold white]SYSTEM DIAGNOSTICS  /  READ-ONLY[/]",
            "[#858585]Live measurements are observations, not proof of root cause.[/]",
            "",
        ]
        warnings = 0
        for key in ("cpu", "memory", "disk"):
            value = float(data[key]["usage_percent"])
            level = "CRITICAL" if value >= 90 else "WARNING" if value >= 75 else "NORMAL"
            color = "#EE9B92" if level == "CRITICAL" else "#DCC18A" if level == "WARNING" else "#90C7AE"
            lines.append(f"[{color}]{level:<8}[/] {key.upper():<7} {value:.1f}%")
            if level != "NORMAL":
                warnings += 1
                why, inspect, action, verify = playbooks[key]
                lines.extend([
                    f"  Context: {why}",
                    f"  Inspect on HOST: {inspect}",
                    f"  Next action: {action}",
                    f"  Verify: {verify}",
                    "",
                ])
        if not warnings:
            lines.extend([
                "",
                "[bold #90C7AE]NO RESOURCE PRESSURE THRESHOLDS TRIGGERED[/]",
                "Measurements are below the configured warning threshold.",
                "Use Processes (2) to inspect current workloads or Preflight (6) to check readiness.",
            ])
        lines.extend([
            "",
            "[#787878]Warning >=75%  /  Critical >=90%  /  Refresh every 5s[/]",
            "[#787878]Suggested commands are for the REAL Linux host; FORGE's command lab is isolated.[/]",
            "[#787878]No host command is executed by this diagnostics screen.[/]",
        ])
        self.query_one("#console", Static).update("\n".join(lines))

    def render_drift(self):
        try:
            result = check_drift()
            status = result["status"]

            if status == "no_baseline":
                message = (
                    "NO BASELINE EXISTS\n\n"
                    "Press B to establish the current configuration "
                    "as the approved baseline."
                )
            elif status == "clean":
                message = (
                    "CLEAN / NO CONFIGURATION DRIFT\n\n"
                    f"Verified {result['checked_files']} tracked files."
                )
            else:
                lines = [
                    f"{item['state']:10} {item['file']}"
                    for item in result["changes"]
                ]
                message = (
                    "CONFIGURATION CHANGES DETECTED\n\n"
                    + "\n".join(lines)
                )

            self.query_one("#console", Static).update(
                "[bold white]CONFIGURATION INTEGRITY[/]\n\n"
                + message
                + "\n\n[#888888]"
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
                "\n".join(lines)
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
