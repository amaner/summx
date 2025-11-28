import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from summx.agent import PaperAgent, PlanExecutor, QueryPlanner
from summx.config import load_config
from summx.llm import get_llm
from summx.sources import get_source_client
from summx.models import PaperResult, SearchPlan

# --- Manual .env loading (Workaround) ---
def _load_dotenv():
    env_path = Path('.') / '.env'
    if env_path.is_file():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ.setdefault(key, value)

_load_dotenv()

# --- Basic Setup ---
app = typer.Typer(
    name="summx",
    help="A CLI for searching and summarizing academic papers with LLMs.",
    add_completion=False,
)
console = Console()

# Configure logging to be less verbose for the user
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def _print_results(plan: SearchPlan, results: List[PaperResult]):
    """Prints the final results in a structured format using Rich."""
    console.print(Panel(f"[bold]Query:[/] {plan.raw_query}", title="Search Plan", border_style="green"))

    if not results:
        console.print("[yellow]No papers found matching your query.[/yellow]")
        return

    for i, result in enumerate(results):
        meta = result.meta
        title_text = f"{i + 1}. {meta.title}"
        author_text = f"[italic]by {', '.join(meta.authors)}[/italic]"
        meta_text = f"Published: {meta.published} | ArXiv ID: {meta.arxiv_id}"

        summary_panel = ""
        console.print(Panel(
            f"[bold cyan]{title_text}[/bold cyan]\n{author_text}\n{meta_text}",
            title=f"Result {i+1}",
            border_style="magenta",
            expand=True
        ))
        if result.summary:
            summary_text = result.summary.raw_markdown
            summary_panel = Panel(summary_text, title="Summary", border_style="blue", expand=True)
            console.print(summary_panel)


async def _run_agent(query: str):
    """The core async function that sets up and runs the agent."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        try:
            progress.add_task("Loading configuration...", total=None)
            config = load_config()

            # 1. Set up all dependencies
            progress.add_task("Initializing LLMs and clients...", total=None)
            planner_llm = get_llm(provider=config.planner_provider, config=config)
            summarizer_llm = get_llm(provider=config.summarizer_provider, config=config)

            source_client = get_source_client(config=config)

            planner = QueryPlanner(llm=planner_llm)
            executor = PlanExecutor(
                source_client=source_client, summarizer_llm=summarizer_llm
            )

            agent = PaperAgent(planner=planner, executor=executor)

            # 2. Run the agent
            progress.add_task(f"Running query: '{query}'...", total=None)
            plan, results = await agent.run(query)

        except Exception as e:
            console.print(f"[bold red]An error occurred:[/] {e}")
            console.print_exception(show_locals=True)
            raise typer.Exit(code=1)

    # 3. Print results outside the progress bar context
    _print_results(plan, results)


@app.command(name="query")
def run_query(query: str = typer.Argument(..., help="The natural language query to search for papers.")):
    """
    Search for and summarize academic papers based on a query.
    """
    asyncio.run(_run_agent(query))


@app.command()
def ui():
    """Launches the Streamlit web UI."""
    # Get the path to the UI's main script
    ui_path = Path(__file__).parent.parent / "ui" / "main.py"
    if not ui_path.exists():
        console.print(f"[bold red]Error:[/] UI script not found at {ui_path}")
        raise typer.Exit(1)

    # Use subprocess to run streamlit, ensuring it's run in the context
    # of the current Python environment.
    try:
        subprocess.run(["streamlit", "run", str(ui_path)], check=True)
    except FileNotFoundError:
        console.print("[bold red]Error:[/] `streamlit` command not found. Is it installed in your environment?")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Failed to launch Streamlit UI:[/] {e}")
        raise typer.Exit(1)

def main():
    app()


if __name__ == "__main__":
    main()
