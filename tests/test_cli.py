from typer.testing import CliRunner

from summx.cli.main import app

runner = CliRunner()

def test_app_runs_query():
    """Tests that the CLI app can be invoked with the query command."""
    # We don't need to check the output, just that it runs without crashing.
    # A more comprehensive test would mock the agent and check the output.
    result = runner.invoke(app, ["query", "test query"])
    assert result.exit_code == 0
