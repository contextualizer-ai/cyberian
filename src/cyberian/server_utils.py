"""Server management utilities for agentapi servers.

Simple functions for discovering, starting, and stopping agentapi server processes.
Extracted from cli.py to be reusable by dashboard and other tools.
"""

import os
import re
import shlex
import socket
import subprocess
from typing import Optional


def get_running_servers() -> list[dict]:
    """Parse ps output and return running agentapi servers.

    Returns:
        List of dicts with keys: pid, port, name, command

    Raises:
        RuntimeError: If ps command fails

    Example:
        >>> servers = get_running_servers()
        >>> for server in servers:
        ...     print(f"{server['name']} on port {server['port']}")
    """
    result = subprocess.run(
        ["ps", "auxwww"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Error running ps command: {result.stderr}")

    # Parse ps output to find agentapi servers
    lines = result.stdout.strip().split("\n")
    servers = []

    for line in lines:
        # Skip header line
        if line.strip().startswith("USER"):
            continue

        # Look for agentapi servers (either "agentapi" or named servers with "server" in command)
        if "agentapi" not in line.lower() and "server" not in line.lower():
            continue

        # Parse the line
        parts = line.split()
        if len(parts) < 11:
            continue

        pid = parts[1]
        # Command is everything from index 10 onwards
        command = " ".join(parts[10:])

        # Only include if this looks like an agentapi server
        if "server" not in command or ("agentapi" not in command and "--port" not in command):
            continue

        # Extract port
        port_match = re.search(r'--port\s+(\d+)', command)
        if not port_match:
            continue

        port = int(port_match.group(1))

        # Extract name (if exec -a was used, it's the first part of command)
        name = parts[10] if parts[10] != "agentapi" else None

        servers.append({
            "pid": pid,
            "name": name,
            "port": port,
            "command": command
        })

    return servers


def resolve_server_name_to_port(name: str) -> int:
    """Resolve a server name to its port by parsing ps output.

    Args:
        name: The server name to look up

    Returns:
        The port number the server is running on

    Raises:
        ValueError: If the server name is not found or no port found

    Example:
        >>> port = resolve_server_name_to_port("my-worker")
        >>> print(f"Server 'my-worker' is on port {port}")
    """
    result = subprocess.run(
        ["ps", "auxwww"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Error running ps command: {result.stderr}")

    # Parse ps output to find the named server
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

        command = " ".join(parts[10:])

        # Check if this line contains the server name
        if parts[10] == name or (name in command and "server" in command):
            # Extract port from --port flag
            port_match = re.search(r'--port\s+(\d+)', command)
            if port_match:
                return int(port_match.group(1))

    raise ValueError(f"No server found with name '{name}'")


def find_available_port(start: int = 4800, max_port: int = 4900) -> int:
    """Find the next available port using socket binding.

    Args:
        start: Starting port to check (default 4800)
        max_port: Maximum port to check (default 4900)

    Returns:
        An available port number

    Raises:
        RuntimeError: If no ports available in range

    Example:
        >>> port = find_available_port()
        >>> print(f"Found available port: {port}")
    """
    # Get currently used ports from running servers
    try:
        servers = get_running_servers()
        used_ports = {s['port'] for s in servers}
    except Exception:
        used_ports = set()

    # Try to bind to each port
    for port in range(start, max_port):
        if port in used_ports:
            continue

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue

    raise RuntimeError(f"No available ports in range {start}-{max_port}")


def start_agentapi_server(
    agent_type: str,
    port: int,
    directory: str,
    name: Optional[str] = None,
    skip_permissions: bool = False,
    allowed_hosts: Optional[str] = None,
    allowed_origins: Optional[str] = None
) -> subprocess.Popen:
    """Start an agentapi server process.

    Args:
        agent_type: Agent type (e.g., "claude", "aider", "cursor")
        port: Port to run the server on
        directory: Working directory for the server
        name: Optional server name (appears in ps with exec -a)
        skip_permissions: If True, add agent-specific skip permissions flags
        allowed_hosts: Optional HTTP allowed hosts (comma-separated)
        allowed_origins: Optional HTTP allowed origins (comma-separated)

    Returns:
        The subprocess.Popen object for the started server

    Raises:
        RuntimeError: If directory doesn't exist

    Example:
        >>> process = start_agentapi_server(
        ...     agent_type="claude",
        ...     port=4800,
        ...     directory="/tmp/my-project",
        ...     name="my-worker"
        ... )
        >>> print(f"Started server with PID: {process.pid}")
    """
    # Validate directory exists
    if not os.path.isdir(directory):
        raise RuntimeError(f"Directory does not exist: {directory}")

    # Build base command
    base_cmd = ["agentapi", "server", agent_type]
    base_cmd.extend(["--port", str(port)])

    if allowed_hosts:
        base_cmd.extend(["--allowed-hosts", allowed_hosts])

    if allowed_origins:
        base_cmd.extend(["--allowed-origins", allowed_origins])

    # Add agent-specific flags after --
    agent_flags = []
    if skip_permissions:
        if agent_type.lower() == "claude":
            agent_flags.append("--dangerously-skip-permissions")
        # Add other agent-specific flags as needed

    if agent_flags:
        base_cmd.append("--")
        base_cmd.extend(agent_flags)

    # Use exec -a to set process name if provided
    if name:
        shell_cmd = f"exec -a {shlex.quote(name)} " + " ".join(shlex.quote(arg) for arg in base_cmd)
        cmd = ["sh", "-c", shell_cmd]
    else:
        cmd = base_cmd

    # Start the process in the specified directory
    process = subprocess.Popen(
        cmd,
        cwd=directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return process


def stop_server_by_port(port: int) -> None:
    """Kill server process listening on specified port.

    Uses lsof to find the PID, then kills it.

    Args:
        port: Port number to find and stop

    Raises:
        RuntimeError: If no process found on port or kill fails

    Example:
        >>> stop_server_by_port(4800)
        # Server on port 4800 is stopped
    """
    # Use lsof to find processes listening on the port
    result = subprocess.run(
        ["lsof", "-ti", f"tcp:{port}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"No process found listening on port {port}")

    # Parse PIDs from lsof output and kill each
    pids = result.stdout.strip().split("\n")
    failed = []

    for pid in pids:
        pid = pid.strip()
        if not pid:
            continue

        kill_result = subprocess.run(
            ["kill", pid],
            capture_output=True,
            text=True
        )

        if kill_result.returncode != 0:
            failed.append((pid, kill_result.stderr))

    if failed:
        errors = "; ".join([f"PID {pid}: {err}" for pid, err in failed])
        raise RuntimeError(f"Failed to stop some processes: {errors}")


def stop_server_by_pid(pid: str) -> None:
    """Kill server process by PID.

    Args:
        pid: Process ID to kill

    Raises:
        RuntimeError: If kill command fails

    Example:
        >>> stop_server_by_pid("12345")
        # Process 12345 is stopped
    """
    result = subprocess.run(
        ["kill", pid],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to kill process {pid}: {result.stderr}")
