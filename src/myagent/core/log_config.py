from rich.markdown import Markdown
from rich.panel import Panel

from rich.syntax import Syntax
from rich.console import Console


class AgentLogger:
    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def log_code(self, code: str):
        self.console.print(
            Panel(Syntax(code, "bash"), title="[green]Coding...", border_style="green")
        )

    def log_md(self, title: str, md: str, border: str):
        self.console.print(Panel(Markdown(md), title=title, border_style=border))

    def log_final_answer(self, answ: str):
        self.log_md("[yellow]Final Answer", answ, "yellow")

    def log_think(self, thoughts: str):
        self.log_md("[blue]Thinking...", thoughts, "blue")

    def log_exeption(self, error: str):
        self.console.print(
            Panel(Syntax(error, "bash"), title="[red]Error", border_style="red")
        )

    def log_observation(self, observation: str):
        self.console.print(
            Panel(
                Syntax(observation, "bash"),
                title="[magenta]Environment...",
                border_style="magenta",
            )
        )

    def log_prompt(self, prompt: str):
        self.console.print(
            Panel(Markdown(prompt), title="[white]You", border_style="white")
        )

