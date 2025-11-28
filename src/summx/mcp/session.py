import asyncio
import json
import logging
import shlex
import subprocess
from typing import Any, Dict, Optional

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
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 1
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self) -> None:
        """Starts the MCP server as a subprocess and connects the client."""
        if self._process and self._process.returncode is None:
            logger.info("MCP server process is already running.")
            return

        command = shlex.split(self.config.mcp_arxiv_command)
        logger.info(f"Starting MCP server with command: {command}")
        try:
            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            await asyncio.sleep(2)  # Give the server a moment to start

            if self._process.returncode is not None:
                stderr_output = await self._process.stderr.read()
                raise RuntimeError(
                    f"MCP server failed to start. Exit code: {self._process.returncode}. Error: {stderr_output.decode()}"
                )

            logger.info("MCP server started successfully.")

        except FileNotFoundError:
            raise RuntimeError(
                f"Command not found: '{command[0]}'. Is 'uv' installed and in your PATH?"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}") from e

    async def stop(self) -> None:
        """Stops the MCP server process."""
        if self._process and self._process.returncode is None:
            logger.info("Stopping MCP server process.")
            self._process.terminate()
            await self._process.wait()
            logger.info("MCP server stopped.")
        self._process = None

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a tool on the running MCP server.

        Args:
            name: The name of the tool to call.
            arguments: A dictionary of arguments for the tool.

        Returns:
            The JSON response from the tool as a dictionary.
        """
        if not self._process or self._process.returncode is not None:
            raise RuntimeError("MCP session is not active. Call start() first.")

        try:
            # 1. Construct and send the JSON-RPC request
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
                "id": self._request_id,
            }
            self._request_id += 1
            request_json = json.dumps(payload).encode('utf-8')
            request_message = f"Content-Length: {len(request_json)}\r\n\r\n".encode('utf-8') + request_json
            
            logger.debug(f"Sending to MCP: {request_message!r}")
            self._process.stdin.write(request_message)
            await self._process.stdin.drain()

            # 2. Read the response from the server's stdout
            # This is a more robust implementation that can handle responses with or without headers.
            first_line_bytes = await self._process.stdout.readline()
            if not first_line_bytes:
                raise RuntimeError("MCP server closed connection unexpectedly.")

            first_line = first_line_bytes.decode('utf-8').strip()
            logger.debug(f"Received from MCP: {first_line}")

            if first_line.startswith("{"):
                # This is a raw JSON response, likely an error notification
                response_json = first_line
            else:
                # This is a full response with headers
                headers = {}
                headers[first_line.split(":", 1)[0].strip().lower()] = first_line.split(":", 1)[1].strip()
                while True:
                    line_bytes = await self._process.stdout.readline()
                    line = line_bytes.decode('utf-8').strip()
                    logger.debug(f"Received from MCP header: {line}")
                    if not line:
                        break  # End of headers
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

                content_length = int(headers.get("content-length", 0))
                if not content_length:
                    raise RuntimeError("MCP response missing or invalid Content-Length header.")

                response_bytes = await self._process.stdout.readexactly(content_length)
                response_json = response_bytes.decode('utf-8')

            logger.debug(f"Received from MCP body: {response_json}")
            response_data = json.loads(response_json)

            # 4. Return the result
            if 'error' in response_data:
                error = response_data['error']
                raise RuntimeError(f"MCP tool '{name}' error: {error.get('message', 'Unknown error')}")

            return response_data.get("result", {})
        except Exception as e:
            raise RuntimeError(f"Error calling MCP tool '{name}': {e}") from e

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
