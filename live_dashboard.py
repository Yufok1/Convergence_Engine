#!/usr/bin/env python3
"""
🧬 CONVERGENCE ENGINE LIVE DASHBOARD
Interactive terminal UI for monitoring the simulation
"""

import json
import time
import os
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.columns import Columns
except ImportError:
    print("Installing rich library...")
    os.system(f"{sys.executable} -m pip install rich")
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.columns import Columns

console = Console()

class LiveDashboard:
    def __init__(self):
        self.data = {}
        self.data_path = Path("data/live_report.json")
        self.engine_log_path = Path(os.environ.get("ENGINE_LOG", "data/unified_entry.log"))
        self.boot_started_at = time.time()
        self.running = True
        self.view = "main"  # main, organisms, alliances, neural, language
        
    def load_data(self):
        """Load fresh data from live_report.json"""
        try:
            with open(self.data_path, 'r') as f:
                self.data = json.load(f)
            return True
        except:
            return False

    def load_boot_log_tail(self, max_lines=18):
        """Load the latest engine boot lines while live_report.json is not ready."""
        try:
            if not self.engine_log_path.exists():
                return [f"Waiting for engine log: {self.engine_log_path}"]
            lines = self.engine_log_path.read_text(errors="replace").splitlines()
            return lines[-max_lines:] if lines else ["Engine log is empty so far."]
        except Exception as exc:
            return [f"Could not read engine log: {exc}"]

    def parse_boot_progress(self, lines):
        """Extract best-effort brain creation progress from noisy boot logs."""
        import re

        current = None
        total = None
        for line in reversed(lines):
            if "Creating brains" not in line:
                continue
            match = re.search(r"(\d+)\s*/\s*(\d+)", line)
            if not match:
                continue
            current = int(match.group(1))
            total_text = match.group(2)
            if len(total_text) > 3 and total_text.startswith("100"):
                total = 100
            else:
                total = int(total_text)
            break
        return current, total

    def make_boot_dashboard(self):
        """Render a dashboard-shaped boot monitor until live_report.json exists."""
        lines = self.load_boot_log_tail()
        current, total = self.parse_boot_progress(lines)
        elapsed = int(time.time() - self.boot_started_at)

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        if current is not None and total:
            pct = min(100, max(0, int((current / max(total, 1)) * 100)))
            filled = max(1, int(pct / 4)) if pct else 0
            bar = "█" * filled + "░" * (25 - filled)
            progress = f"[cyan]{bar}[/] [bold]{current}/{total}[/] brains ({pct}%)"
        else:
            progress = "[yellow]Waiting for first boot progress signal[/]"

        body = "\n".join(lines[-18:])
        layout["header"].update(Panel(
            "[bold cyan]CONVERGENCE ENGINE[/] │ [yellow]Booting full facility[/]",
            style="bold white on dark_blue",
            box=box.DOUBLE
        ))
        layout["body"].update(Panel(
            f"{progress}\n\n[dim]Waiting for:[/] {self.data_path}\n"
            f"[dim]Engine log:[/] {self.engine_log_path}\n"
            f"[dim]Elapsed:[/] {elapsed}s\n\n{body}",
            title="Boot Monitor",
            border_style="yellow"
        ))
        layout["footer"].update(Panel(
            "[dim]Dashboard will switch automatically when live_report.json is created.[/]",
            style="dim"
        ))
        return layout
    
    def make_header(self):
        """Create header panel"""
        ts = self.data.get('timestamp', 'Unknown')[:19]
        config = self.data.get('config_name', 'Unknown')
        return Panel(
            f"[bold cyan]🧬 CONVERGENCE ENGINE[/] │ [dim]{config}[/] │ [yellow]{ts}[/]",
            style="bold white on dark_blue",
            box=box.DOUBLE
        )
    
    def make_population_panel(self):
        """Population stats panel"""
        pop = self.data.get('population', {})
        total = pop.get('total_organisms', 0)
        active = pop.get('active_organisms', 0)
        fallen = pop.get('fallen_organisms', 0)
        fitness = pop.get('fitness_mean', 0)
        age_max = pop.get('age_max', 0)
        gen_max = pop.get('generation_max', 0)
        
        content = f"""[bold green]{total:,}[/] organisms
[dim]Active:[/] {active:,} │ [red]Fallen:[/] {fallen}
[dim]Fitness:[/] [cyan]{fitness:.4f}[/]
[dim]Age Max:[/] {age_max} │ [dim]Gen:[/] {gen_max}"""
        
        return Panel(content, title="👥 Population", border_style="green")
    
    def make_highlander_panel(self):
        """Highlander tournament panel"""
        hl = self.data.get('highlander', {})
        phase = hl.get('phase', 'unknown')
        round_num = hl.get('round_number', 0)
        elims = hl.get('eliminations_total', 0)
        battles = hl.get('total_battles', 0)
        
        phase_color = {
            'germination': 'yellow',
            'competition': 'red',
            'evolution': 'green',
            'convergence': 'cyan'
        }.get(phase, 'white')
        
        content = f"""[{phase_color}]◉ {phase.upper()}[/]
[dim]Round:[/] [bold]{round_num}[/] │ [dim]Battles:[/] {battles}
[red]Eliminations:[/] {elims}"""
        
        return Panel(content, title="⚔️ Highlander", border_style="red")
    
    def make_alliance_panel(self):
        """Alliance system panel"""
        al = self.data.get('alliances', {})
        active = al.get('active_alliances', 0)
        members = al.get('total_members', 0)
        largest = al.get('largest_alliance_size', 0)
        warchiefs = al.get('warchief_count', 0)
        territories = al.get('territories_claimed', 0)
        legends = al.get('legends_recorded', 0)
        
        content = f"""[bold]{active}[/] alliances │ [cyan]{members}[/] members
[dim]Largest:[/] {largest} │ [gold1]Chiefs:[/] {warchiefs}
[dim]Territories:[/] {territories}/6 │ [dim]Legends:[/] {legends}"""
        
        return Panel(content, title="🤝 Alliances", border_style="blue")
    
    def make_neural_panel(self):
        """Neural network panel"""
        nn = self.data.get('neural', {})
        brains = nn.get('organisms_with_brains', 0)
        epsilon = nn.get('avg_epsilon', 0)
        exp = nn.get('experience_buffer_total', 0)
        steps = nn.get('total_training_steps', 0)
        
        # Epsilon bar (1.0 = random, 0.0 = learned)
        learned_pct = (1 - epsilon) * 100
        
        content = f"""[bold]{brains:,}[/] brains │ [dim]Steps:[/] {steps:,}
[dim]Experience:[/] [cyan]{exp:,}[/]
[dim]Learned:[/] [green]{learned_pct:.0f}%[/] [dim](ε={epsilon:.3f})[/]"""
        
        return Panel(content, title="🧠 Neural", border_style="magenta")
    
    def make_language_panel(self):
        """Language emergence panel"""
        lang = self.data.get('language', {})
        vocab = lang.get('total_vocabulary_words', 0)
        unique = lang.get('unique_words_across_pop', 0)
        highest = lang.get('highest_mastery_achieved', 0)
        
        # Mastery breakdown
        m0 = lang.get('mastery_level_0', 0)
        m1 = lang.get('mastery_level_1', 0)
        m2 = lang.get('mastery_level_2', 0)
        m3 = lang.get('mastery_level_3', 0)
        m4 = lang.get('mastery_level_4', 0)
        
        mastery_bar = f"[dim]0:[/]{m0} [blue]1:[/]{m1} [cyan]2:[/]{m2} [green]3:[/]{m3} [gold1]4:[/]{m4}"
        
        mastery_color = ['white', 'blue', 'cyan', 'green', 'gold1'][min(highest, 4)]
        
        content = f"""[dim]Vocab:[/] [bold]{vocab:,}[/] │ [dim]Unique:[/] {unique}
[dim]Highest Mastery:[/] [{mastery_color}]★ LEVEL {highest}[/]
{mastery_bar}"""
        
        return Panel(content, title="📚 Language", border_style="yellow")
    
    def make_network_panel(self):
        """Network topology panel"""
        net = self.data.get('network', {})
        connections = net.get('connections', 0)
        density = net.get('network_density', 0)
        communities = net.get('communities', 0)
        clustering = net.get('clustering_coefficient', 0)
        
        content = f"""[dim]Connections:[/] [bold]{connections:,}[/]
[dim]Density:[/] {density:.4f} │ [dim]Clustering:[/] {clustering:.4f}
[dim]Communities:[/] [cyan]{communities}[/]"""
        
        return Panel(content, title="🕸️ Network", border_style="cyan")
    
    def make_resources_panel(self):
        """System resources panel"""
        res = self.data.get('resources', {})
        cpu = res.get('cpu_percent', 0)
        mem_gb = res.get('memory_used_gb', 0)
        mem_total = res.get('memory_total_gb', 1)
        gpu_mb = res.get('gpu_memory_used_mb', 0)
        gpu_total = res.get('gpu_memory_total_mb', 1)
        breath = res.get('breath_cycle', 0)
        uptime = res.get('uptime_seconds', 0) / 60
        
        cpu_color = 'green' if cpu < 70 else 'yellow' if cpu < 90 else 'red'
        
        content = f"""[{cpu_color}]CPU: {cpu:.0f}%[/] │ [dim]RAM:[/] {mem_gb:.1f}/{mem_total:.0f}GB
[dim]GPU:[/] {gpu_mb:.0f}/{gpu_total:.0f}MB
[dim]Breath:[/] {breath} │ [dim]Uptime:[/] {uptime:.0f}m"""
        
        return Panel(content, title="💻 Resources", border_style="white")
    
    def make_events_panel(self):
        """Recent events panel"""
        events = self.data.get('events', {})
        total = events.get('total_events', 0)
        last_hr = events.get('events_last_hour', 0)
        
        # Get event breakdown
        by_type = events.get('events_by_type', {})
        top_events = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]
        
        event_lines = []
        for evt, count in top_events:
            short_name = evt.replace('_', ' ')[:20]
            event_lines.append(f"[dim]{short_name}:[/] {count:,}")
        
        content = f"""[dim]Total:[/] [bold]{total:,}[/] │ [dim]Last hr:[/] {last_hr:,}
""" + "\n".join(event_lines)
        
        return Panel(content, title="📡 Events", border_style="dim")
    
    def make_behaviors_panel(self):
        """Behavior distribution panel"""
        lang = self.data.get('language', {})
        behaviors = lang.get('dominant_behaviors', {})
        
        if not behaviors:
            return Panel("[dim]No behavior data[/]", title="🎭 Behaviors")
        
        total = sum(behaviors.values())
        lines = []
        colors = {
            'explorer': 'green',
            'hermit': 'blue', 
            'diplomat': 'cyan',
            'warrior': 'red',
            'conserver': 'yellow'
        }
        
        for beh, count in sorted(behaviors.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            color = colors.get(beh, 'white')
            bar_len = int(pct / 5)
            bar = '█' * bar_len
            lines.append(f"[{color}]{beh:10}[/] [{color}]{bar}[/] {pct:.0f}%")
        
        return Panel("\n".join(lines), title="🎭 Behaviors", border_style="magenta")
    
    def make_dashboard(self):
        """Assemble the full dashboard"""
        if not self.load_data():
            return self.make_boot_dashboard()
        
        # Build layout
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="center"),
            Layout(name="right")
        )
        
        # Left column
        layout["left"].split_column(
            Layout(self.make_population_panel()),
            Layout(self.make_highlander_panel()),
            Layout(self.make_alliance_panel())
        )
        
        # Center column  
        layout["center"].split_column(
            Layout(self.make_neural_panel()),
            Layout(self.make_language_panel()),
            Layout(self.make_behaviors_panel())
        )
        
        # Right column
        layout["right"].split_column(
            Layout(self.make_network_panel()),
            Layout(self.make_resources_panel()),
            Layout(self.make_events_panel())
        )
        
        layout["header"].update(self.make_header())
        layout["footer"].update(Panel(
            "[dim]Press [bold]Ctrl+C[/] to exit │ Auto-refresh every 2s[/]",
            style="dim"
        ))
        
        return layout
    
    def run(self):
        """Run the live dashboard"""
        console.clear()

        use_screen = os.environ.get("CONVERGENCE_DASHBOARD_SCREEN", "").strip().lower()
        screen_mode = use_screen not in {"0", "false", "no", "off"} and console.is_terminal
        with Live(self.make_dashboard(), refresh_per_second=0.5, screen=screen_mode) as live:
            try:
                while self.running:
                    time.sleep(2)
                    live.update(self.make_dashboard())
            except KeyboardInterrupt:
                self.running = False
        
        console.print("\n[bold green]Dashboard closed.[/]")


def main():
    dashboard = LiveDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
