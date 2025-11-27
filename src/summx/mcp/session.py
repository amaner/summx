import asyncio
import logging
import shlex
import subprocess
from typing import Any, Dict, Optional

#from mcp import Client
from mcp.client.session import ClientSession as Client

from summx.config import SummXConfig

logger = logging.getLogger(__name__)


class McpSession:
    """
    Manages the lifecycle and communication with a local MCP server process.
    """

    def __init__(self, config: SummXConfig):
        """
        Initializes the McpSession with configuration.

        Args:
            config: The application configuration object.
        """
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._client: Optional[Client] = None

    async def start(self) -> None:
        """Starts the MCP server as a subprocess and connects the client."""
        if self._process and self._process.poll() is None:
            logger.info("MCP server process is already running.")
            return

        command = shlex.split(self.config.mcp_arxiv_command)
        logger.info(f"Starting MCP server with command: {command}")
        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Give the server a moment to start up
            await asyncio.sleep(3)

            if self._process.poll() is not None:
                stderr = self._process.stderr.read() if self._process.stderr else ""
                raise RuntimeError(
                    f"MCP server failed to start. Exit code: {self._process.returncode}. Error: {stderr}"
                )

            logger.info("MCP server started successfully.")
            self._client = Client()

        except FileNotFoundError:
            raise RuntimeError(
                f"Command not found: '{command[0]}'. Is 'uv' installed and in your PATH?"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}") from e

    async def stop(self) -> None:
        """Stops the MCP server process."""
        if self._process and self._process.poll() is None:
            logger.info("Stopping MCP server process.")
            self._process.terminate()
            try:
                await asyncio.to_thread(self._process.wait, timeout=5)
                logger.info("MCP server stopped.")
            except subprocess.TimeoutExpired:
                logger.warning("MCP server did not terminate gracefully. Killing.")
                self._process.kill()
        self._process = None
        self._client = None

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a tool on the running MCP server.

        Args:
            name: The name of the tool to call.
            arguments: A dictionary of arguments for the tool.

        Returns:
            The JSON response from the tool as a dictionary.
        """
        if not self._client or not self._process or self._process.poll() is not None:
            raise RuntimeError("MCP session is not active. Call start() first.")

        try:
            response = await self._client.call_tool(tool_name=name, arguments=arguments)
            return response
        except Exception as e:
            raise RuntimeError(f"Error calling MCP tool '{name}': {e}") from e

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
