"""FastAPI backend for Cyberian Dashboard."""

import asyncio
import logging
import re
import subprocess
from typing import List, Optional

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServerInfo(BaseModel):
    """Information about a running agentapi server."""

    pid: str
    port: int
    name: Optional[str] = None
    command: str
    status: str = "running"
    url: str


class ServerStatusResponse(BaseModel):
    """Response for server status check."""

    port: int
    status: str
    response_time: Optional[float] = None
    error: Optional[str] = None


class ServerStartRequest(BaseModel):
    """Request to start a new agentapi server."""

    directory: str
    name: Optional[str] = None
    port: Optional[int] = None
    model: Optional[str] = None  # This now represents agent type (claude, openai, aider, etc.)


app = FastAPI(title="Cyberian Dashboard API", version="0.1.0")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store WebSocket connections for real-time updates
active_connections: List[WebSocket] = []


def parse_servers() -> List[ServerInfo]:
    """Parse running agentapi servers using ps command.

    Returns:
        List of ServerInfo objects for running servers
    """
    servers = []

    # Run ps command to get process list
    try:
        result = subprocess.run(
            ["ps", "auxwww"],
            capture_output=True,
            text=True,
            timeout=5
        )
    except subprocess.TimeoutExpired:
        logger.error("ps command timed out")
        raise HTTPException(status_code=500, detail="Process listing timed out")
    except Exception as e:
        logger.error(f"Error running ps command: {e}")
        raise HTTPException(status_code=500, detail=f"Error running ps command: {str(e)}")

    if result.returncode != 0:
        logger.error(f"ps command failed: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Error running ps command: {result.stderr}")

    lines = result.stdout.strip().split("\n")

    for line in lines:
        # Skip header line
        if line.strip().startswith("USER"):
            continue

        # Look for agentapi servers
        if "agentapi" not in line.lower() and "server" not in line.lower():
            continue

        parts = line.split()
        if len(parts) < 11:
            continue

        pid = parts[1]
        command = " ".join(parts[10:])

        # Only include if this looks like an agentapi server
        if "server" not in command or ("agentapi" not in command and "--port" not in command):
            continue

        # Extract port
        port_match = re.search(r'--port[= ](\d+)', command)
        if not port_match:
            # Try to find port in other formats
            port_match = re.search(r':(\d{4,5})', command)
            if not port_match:
                continue

        port = int(port_match.group(1))

        # Extract name if present
        name_match = re.search(r'--name[= ]([^\s]+)', command)
        name = name_match.group(1) if name_match else None

        # If no explicit name, check if command starts with a custom name
        if not name and not command.startswith("agentapi"):
            # Extract the first word as potential name
            first_word = command.split()[0]
            if first_word and "/" not in first_word:
                name = first_word

        servers.append(ServerInfo(
            pid=pid,
            port=port,
            name=name,
            command=command,
            status="running",
            url=f"http://localhost:{port}"
        ))

    return sorted(servers, key=lambda s: s.port)


async def check_server_health(port: int) -> ServerStatusResponse:
    """Check if a server is responding at the given port.

    Args:
        port: Server port to check

    Returns:
        ServerStatusResponse with health check results
    """
    import httpx
    import time

    url = f"http://localhost:{port}/health"
    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=2.0)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return ServerStatusResponse(
                    port=port,
                    status="healthy",
                    response_time=response_time
                )
            else:
                return ServerStatusResponse(
                    port=port,
                    status="unhealthy",
                    response_time=response_time,
                    error=f"Status code: {response.status_code}"
                )
    except Exception as e:
        return ServerStatusResponse(
            port=port,
            status="unreachable",
            error=str(e)
        )


@app.get("/api/servers", response_model=List[ServerInfo])
async def list_servers():
    """List all running agentapi servers."""
    try:
        servers = parse_servers()
        logger.info(f"Found {len(servers)} servers")
        return servers
    except Exception as e:
        logger.error(f"Error listing servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list servers: {str(e)}")


@app.get("/api/server/{port}/status", response_model=ServerStatusResponse)
async def get_server_status(port: int):
    """Get the health status of a specific server."""
    return await check_server_health(port)


@app.get("/api/server/{port}/agent-status")
async def get_agent_status(port: int):
    """Proxy request to get agent status from agentapi server."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:{port}/status", timeout=2.0)
            return response.json()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Server unreachable: {str(e)}",
            "conversation_id": None
        }


@app.get("/api/server/{port}/messages")
async def get_server_messages(port: int, last: Optional[int] = None):
    """Proxy request to get messages from agentapi server."""
    import httpx
    try:
        url = f"http://localhost:{port}/messages"
        if last:
            url += f"?last={last}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=2.0)
            data = response.json()
            return {"messages": data.get("messages", [])}
    except Exception as e:
        return {"messages": [], "error": str(e)}


@app.post("/api/server/{port}/message")
async def send_server_message(port: int, request: dict):
    """Proxy request to send a message to agentapi server.

    Expects format: {"content": "message text", "type": "user"}
    """
    import httpx

    logger = logging.getLogger(__name__)
    logger.info(f"Sending message to port {port}: {request}")

    try:
        # Ensure the message has the correct format
        if "type" not in request:
            request["type"] = "user"  # Default to user type if not specified

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:{port}/message",
                json=request,
                timeout=30.0,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error sending message to port {port}: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Agent server error: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error sending message to port {port}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot reach agent server on port {port}: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error sending message to port {port}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@app.post("/api/server/{port}/stop")
async def stop_server(port: int):
    """Stop a specific agentapi server."""
    servers = parse_servers()
    server = next((s for s in servers if s.port == port), None)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server on port {port} not found")

    # Kill the process
    result = subprocess.run(
        ["kill", server.pid],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {result.stderr}")

    # Notify WebSocket clients
    await notify_clients({"action": "server_stopped", "port": port})

    return {"status": "stopped", "port": port, "pid": server.pid}


def find_next_available_port(start_port: int = 4800, max_port: int = 4900) -> int:
    """Find the next available port in the range."""
    servers = parse_servers()
    used_ports = {s.port for s in servers}

    for port in range(start_port, max_port):
        if port not in used_ports:
            # Also check if port is actually available
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', port))
                    return port
                except OSError:
                    continue

    raise HTTPException(status_code=503, detail=f"No available ports in range {start_port}-{max_port}")


@app.post("/api/server/start")
async def start_server(request: ServerStartRequest):
    """Start a new agentapi server.

    Args:
        request: Server configuration including directory, optional name and port

    Returns:
        Information about the started server
    """
    import os
    from pathlib import Path

    # Validate directory exists
    if not os.path.isdir(request.directory):
        raise HTTPException(status_code=400, detail=f"Directory does not exist: {request.directory}")

    # Generate name from directory if not provided
    if not request.name:
        # Get the last part of the directory path as name
        dir_path = Path(request.directory)
        request.name = dir_path.name.replace('_', '-').replace(' ', '-').lower()
        # Ensure name is valid (alphanumeric and hyphens only)
        request.name = re.sub(r'[^a-z0-9-]', '', request.name)
        if not request.name:
            request.name = "server"

    # Find available port if not provided
    if not request.port:
        try:
            request.port = find_next_available_port()
            logger.info(f"Auto-assigned port {request.port} for new server")
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    # Build the command - agentapi requires an agent type
    # The 'model' field from frontend is actually the agent type
    agent_type = request.model if request.model else "claude"  # Default to claude

    base_cmd = [
        "agentapi",
        "server",
        agent_type,  # Agent type is required positional argument
        "--port", str(request.port)
    ]

    # Use exec -a to set the process name (shows in ps)
    if request.name:
        import shlex
        # Build shell command: exec -a <name> agentapi ...
        shell_cmd = f"exec -a {shlex.quote(request.name)} " + " ".join(shlex.quote(arg) for arg in base_cmd)
        cmd = ["sh", "-c", shell_cmd]
        logger.info(f"Starting server with name '{request.name}': {shell_cmd}")
    else:
        cmd = base_cmd
        logger.info(f"Starting server with command: {' '.join(cmd)}")

    try:
        # Start the server process in the specified directory
        process = subprocess.Popen(
            cmd,
            cwd=request.directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True  # Detach from parent process
        )

        # Wait a moment to check if process started successfully
        await asyncio.sleep(1)

        # Check if process is still running
        if process.poll() is not None:
            # Process ended, get error
            stdout, stderr = process.communicate()
            error_msg = stderr or stdout or "Failed to start server"
            logger.error(f"Server failed to start: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Server failed to start: {error_msg}")

        logger.info(f"Started server '{request.name}' on port {request.port} with PID {process.pid}")

        # Notify WebSocket clients
        await notify_clients({"action": "server_started", "port": request.port, "name": request.name})

        return {
            "status": "started",
            "port": request.port,
            "name": request.name,
            "pid": process.pid,
            "directory": request.directory,
            "url": f"http://localhost:{request.port}"
        }

    except subprocess.SubprocessError as e:
        logger.error(f"Failed to start server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info("WebSocket connection established")

    try:
        # Send initial server list
        try:
            servers = parse_servers()
            await websocket.send_json({
                "type": "server_list",
                "servers": [s.model_dump() for s in servers]
            })
        except Exception as e:
            logger.error(f"Error sending initial server list: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Failed to get server list: {str(e)}"
            })

        # Keep connection alive and send periodic updates
        while True:
            # Wait for client message or timeout
            try:
                # Use receive with timeout to detect disconnects
                await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                # Timeout is normal, send update
                try:
                    servers = parse_servers()
                    await websocket.send_json({
                        "type": "server_list",
                        "servers": [s.model_dump() for s in servers]
                    })
                except Exception as e:
                    logger.error(f"Error updating server list: {e}")
                    # Don't crash the connection, just log the error

    except Exception as e:
        logger.info(f"WebSocket disconnected: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info("WebSocket connection closed")


async def notify_clients(message: dict):
    """Notify all connected WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            pass


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Cyberian Dashboard API",
        "version": "0.1.0",
        "endpoints": [
            "/api/servers",
            "/api/server/{port}/status",
            "/api/server/{port}/stop",
            "/ws"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)