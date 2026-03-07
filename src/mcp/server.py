import asyncio
import json
from pathlib import Path
from typing import Dict

from ..game.state import GameState
from .tools import MCPTools
from .security import generate_self_signed_cert, create_ssl_context


class MCPServer:
    """
    Secure local MCP server for AI agents.
    Listens on 127.0.0.1:8443 with TLS.
    Protocol: newline-delimited JSON-RPC 2.0.
    """

    def __init__(
        self, game_state: GameState, host: str = "127.0.0.1", port: int = 8443
    ):
        self.game_state = game_state
        self.host = host
        self.port = port
        self.tools = MCPTools(game_state)

        cert_dir = Path("certs")
        cert_dir.mkdir(exist_ok=True)
        cert_path = cert_dir / "cert.pem"
        key_path = cert_dir / "key.pem"

        if not cert_path.exists() or not key_path.exists():
            generate_self_signed_cert(cert_path, key_path)

        self.ssl_context = create_ssl_context(cert_path, key_path)

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle a single MCP client connection"""
        addr = writer.get_extra_info("peername")
        print(f"MCP client connected: {addr}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                try:
                    request = json.loads(data.decode())
                except json.JSONDecodeError as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": f"Parse error: {e}"},
                    }
                    writer.write((json.dumps(response) + "\n").encode())
                    await writer.drain()
                    continue

                response = await self._process_request(request)
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()

        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"Client disconnected: {addr}")

    async def _process_request(self, request: Dict) -> Dict:
        """Dispatch JSON-RPC 2.0 request to the appropriate MCP tool"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "get_state":
                result = self.tools.get_state()
            elif method == "submit_action":
                result = self.tools.submit_action(
                    params.get("action"),
                    params.get("targets", []),
                    params.get("parameters", {}),
                )
            elif method == "request_advice":
                result = self.tools.request_advice(params.get("phase", "intel"))
            elif method == "list_tools":
                result = self.tools.list_tools()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }

            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(e)},
            }

    async def start(self):
        """Start the MCP server and serve forever"""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            ssl=self.ssl_context,
        )

        addr = server.sockets[0].getsockname()
        print(f"MCP Server running on https://{addr[0]}:{addr[1]}")
        print("AI agents connect via: wss://localhost:8443")

        async with server:
            await server.serve_forever()
