"""CLI interface for cyberian."""

import csv
import io
import json
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Literal

import httpx
import typer
import yaml
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

app = typer.Typer(help="cyberian: Wrapper for agentapi for pipelines")

# Server sub-app for grouping server-related commands
server_app = typer.Typer(help="Manage agentapi servers")
app.add_typer(server_app, name="server")

# Farm sub-app for managing multiple servers
farm_app = typer.Typer(help="Manage farms of agentapi servers")
app.add_typer(farm_app, name="farm")


@app.command()
def message(
    content: Annotated[str, typer.Argument(help="Message content to send to the agent")],
    msg_type: Annotated[str, typer.Option("--type", "-t", help="Message type")] = "user",
    host: Annotated[str, typer.Option("--host", "-H", help="Agent API host")] = "localhost",
    port: Annotated[int, typer.Option("--port", "-P", help="Agent API port")] = 3284,
    sync: Annotated[bool, typer.Option("--sync", "-s", help="Wait for agent response and return last agent message")] = False,
    timeout: Annotated[int, typer.Option("--timeout", "-T", help="Timeout in seconds when using --sync")] = 60,
    poll_interval: Annotated[float, typer.Option("--poll-interval", help="Status polling interval in seconds when using --sync")] = 2.0,
):
    """Send a message to the agent API.

    This command wraps the agentapi message endpoint, allowing you to send
    messages to a running agent.

    Example:
        >>> # cyberian message "Hello, agent!"
        >>> # cyberian message "System init" --type system --host example.com --port 8080
        >>> # cyberian message "What is 2+2?" --sync
        >>> # cyberian message "Long task" --sync --timeout 120
    """
    url = f"http://{host}:{port}/message"
    payload = {"content": content, "type": msg_type}

    response = httpx.post(url, content=json.dumps(payload), headers={"Content-Type": "application/json"})
    response.raise_for_status()

    if not sync:
        result = response.json()
        typer.echo(json.dumps(result, indent=2))
        return

    # Sync mode: wait for stable status, then return last agent message
    status_url = f"http://{host}:{port}/status"
    messages_url = f"http://{host}:{port}/messages"

    start_time = time.time()

    # Poll status until stable or timeout
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            typer.echo(f"Error: Timeout exceeded ({timeout}s) waiting for agent to finish processing", err=True)
            raise typer.Exit(1)

        status_response = httpx.get(status_url)
        status_response.raise_for_status()
        status_data = status_response.json()

        # Check if status is stable (not processing/busy)
        agent_status = status_data.get("status", "").lower()
        if agent_status in ["idle", "ready", "stable", "waiting"]:
            break

        time.sleep(poll_interval)

    # Fetch messages and find last agent message
    messages_response = httpx.get(messages_url)
    messages_response.raise_for_status()
    messages_data = messages_response.json()

    messages_list = messages_data.get("messages", [])

    # Find last message from agent (not from user)
    last_agent_message = None
    for msg in reversed(messages_list):
        role = msg.get("role", "").lower()
        if role in ["agent", "assistant", "system"]:
            last_agent_message = msg
            break

    if last_agent_message:
        typer.echo(last_agent_message.get("content", ""))
    else:
        typer.echo("No agent response found", err=True)
        raise typer.Exit(1)


@app.command()
def messages(
    host: Annotated[str, typer.Option("--host", "-H", help="Agent API host")] = "localhost",
    port: Annotated[int, typer.Option("--port", "-P", help="Agent API port")] = 3284,
    output_format: Annotated[
        Literal["json", "yaml", "csv"],
        typer.Option("--format", "-f", help="Output format")
    ] = "json",
    last: Annotated[
        int | None,
        typer.Option("--last", "-l", help="Get only the last N messages")
    ] = None,
):
    """Retrieve all messages from the agent API.

    This command wraps the agentapi /messages endpoint to retrieve
    the conversation history.

    Example:
        >>> # cyberian messages
        >>> # cyberian messages --format yaml
        >>> # cyberian messages --last 5
        >>> # cyberian messages --format csv --last 10
        >>> # cyberian messages --host example.com --port 8080
    """
    url = f"http://{host}:{port}/messages"

    response = httpx.get(url)
    response.raise_for_status()

    result = response.json()

    # Apply limit if requested
    if last is not None and "messages" in result:
        result["messages"] = result["messages"][-last:]

    # Format output based on requested format
    if output_format == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output_format == "yaml":
        typer.echo(yaml.dump(result, default_flow_style=False, sort_keys=False))
    elif output_format == "csv":
        if "messages" in result and result["messages"]:
            output = io.StringIO()

            # Get all keys from all messages for comprehensive headers
            all_keys = set()
            for msg in result["messages"]:
                all_keys.update(msg.keys())
            fieldnames = sorted(all_keys)

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(result["messages"])

            typer.echo(output.getvalue().strip())
        else:
            typer.echo("No messages to display")


@app.command()
def status(
    host: Annotated[str, typer.Option("--host", "-H", help="Agent API host")] = "localhost",
    port: Annotated[int, typer.Option("--port", "-P", help="Agent API port")] = 3284,
):
    """Check the status of the agent API.

    This command wraps the agentapi /status endpoint to check if
    the server is running and get its status information.

    Example:
        >>> # cyberian status
        >>> # cyberian status --host example.com --port 8080
    """
    url = f"http://{host}:{port}/status"

    response = httpx.get(url)
    response.raise_for_status()

    result = response.json()
    typer.echo(json.dumps(result, indent=2))


@server_app.command(name="start")
def start_server(
    agent: Annotated[
        str,
        typer.Argument(help="Agent type (e.g., aider, claude, cursor, goose)")
    ] = "custom",
    port: Annotated[int, typer.Option("--port", "-p", help="Port to run the server on")] = 3284,
    skip_permissions: Annotated[
        bool,
        typer.Option("--skip-permissions", "-s", help="Skip permission checks (translates to agent-specific flags)")
    ] = False,
    allowed_hosts: Annotated[
        str | None,
        typer.Option("--allowed-hosts", help="HTTP allowed hosts (comma-separated)")
    ] = None,
    allowed_origins: Annotated[
        str | None,
        typer.Option("--allowed-origins", help="HTTP allowed origins (comma-separated)")
    ] = None,
    dir: Annotated[
        str | None,
        typer.Option("--dir", "-d", help="Directory to change to before starting the server")
    ] = None,
):
    """Start an agentapi server.

    This command initiates an agentapi server process with the specified
    agent type and port. Optionally change to a specific directory before
    starting the server.

    Example:
        >>> # cyberian server start
        >>> # cyberian server start claude --port 8080
        >>> # cyberian server start aider -p 9000
        >>> # cyberian server start --dir /path/to/project
        >>> # cyberian server start claude --dir /my/project --port 8080
        >>> # cyberian server start claude --skip-permissions
    """
    # Change to specified directory if provided
    if dir:
        os.chdir(dir)
        typer.echo(f"Changed directory to: {dir}")

    # Build base command with agent
    cmd = ["agentapi", "server", agent]

    # Add cyberian's own options (these go before --)
    cmd.extend(["--port", str(port)])

    if allowed_hosts:
        cmd.extend(["--allowed-hosts", allowed_hosts])

    if allowed_origins:
        cmd.extend(["--allowed-origins", allowed_origins])

    # Add agent-specific flags (these go after --)
    agent_flags = []
    if skip_permissions:
        if agent.lower() == "claude":
            agent_flags.append("--dangerously-skip-permissions")
        # Add other agent-specific flags here as needed
        # elif agent.lower() == "aider":
        #     agent_flags.append("--yes")

    if agent_flags:
        cmd.append("--")
        cmd.extend(agent_flags)

    typer.echo(f"Starting agentapi server ({agent}) on port {port}...")
    process = subprocess.Popen(cmd)

    typer.echo(f"Server started with PID: {process.pid}")


@server_app.command(name="list")
def list_servers():
    """List all running agentapi servers.

    This command uses `ps` to find all running agentapi processes
    and displays their process IDs and command lines.

    Example:
        >>> # cyberian server list
    """
    # Use ps to find agentapi processes
    # -e: all processes
    # -o pid,command: show PID and full command line
    result = subprocess.run(
        ["ps", "-e", "-o", "pid,command"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        typer.echo(f"Error running ps command: {result.stderr}", err=True)
        raise typer.Exit(1)

    # Filter lines containing 'agentapi'
    lines = result.stdout.strip().split("\n")
    agentapi_processes = []

    for line in lines:
        if "agentapi" in line.lower() and "grep" not in line.lower():
            agentapi_processes.append(line.strip())

    if not agentapi_processes:
        typer.echo("No agentapi servers found running")
        return

    # Display header
    typer.echo("Running agentapi servers:")
    typer.echo("-" * 80)

    # Display processes (skip the first one if it's the ps header)
    for proc in agentapi_processes:
        if proc and not proc.startswith("PID"):
            typer.echo(proc)


@server_app.command(name="stop")
def stop_server(
    pid: Annotated[
        str | None,
        typer.Argument(help="Process ID of the agentapi server to stop")
    ] = None,
    port: Annotated[
        int | None,
        typer.Option("--port", "-p", help="Port number to find and stop the agentapi server")
    ] = None,
    all_servers: Annotated[
        bool,
        typer.Option("--all", help="Stop all running agentapi servers")
    ] = False,
):
    """Stop a running agentapi server.

    Stop an agentapi server by either specifying its PID directly, by
    finding the process using a specific port, or by stopping all servers.
    If no arguments are provided, defaults to stopping the server on port 3284.

    Example:
        >>> # cyberian server stop              # stops server on default port 3284
        >>> # cyberian server stop 12345        # stops server with PID 12345
        >>> # cyberian server stop --port 8080  # stops server on port 8080
        >>> # cyberian server stop --all        # stops all agentapi servers
    """
    pids_to_kill: list[str] = []

    if all_servers:
        # Find all agentapi processes using ps (similar to list-servers)
        result = subprocess.run(
            ["ps", "-e", "-o", "pid,command"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            typer.echo(f"Error running ps command: {result.stderr}", err=True)
            raise typer.Exit(1)

        # Filter lines containing 'agentapi'
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if "agentapi" in line.lower() and "grep" not in line.lower():
                # Skip the header line
                if line.strip() and not line.strip().startswith("PID"):
                    # Extract PID (first field)
                    parts = line.strip().split(None, 1)
                    if parts:
                        pids_to_kill.append(parts[0])

        if not pids_to_kill:
            typer.echo("No agentapi servers found running")
            return

        typer.echo(f"Found {len(pids_to_kill)} agentapi server(s) to stop")
    elif pid:
        pids_to_kill = [pid]
    else:
        # Default to port 3284 if neither PID nor port nor --all specified
        if port is None:
            port = 3284

        # Find PIDs using the specified port
        # Use lsof to find processes listening on the port
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0 or not result.stdout.strip():
            typer.echo(f"No process found listening on port {port}", err=True)
            raise typer.Exit(1)

        # Parse PIDs from lsof output
        pids_to_kill = result.stdout.strip().split("\n")
        typer.echo(f"Found {len(pids_to_kill)} process(es) on port {port}")

    # Kill each process
    failed = []
    for pid_to_kill in pids_to_kill:
        pid_to_kill = pid_to_kill.strip()
        if not pid_to_kill:
            continue

        result = subprocess.run(
            ["kill", pid_to_kill],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            typer.echo(f"Failed to kill process {pid_to_kill}: {result.stderr}", err=True)
            failed.append(pid_to_kill)
        else:
            typer.echo(f"Successfully stopped process {pid_to_kill}")

    if failed:
        typer.echo(f"Failed to stop {len(failed)} process(es)", err=True)
        raise typer.Exit(1)


# ============================================================================
# Farm Commands
# ============================================================================

@farm_app.command(name="start")
def start_farm(
    farm_file: Annotated[str, typer.Argument(help="Path to farm configuration YAML file")],
):
    """Start a farm of agentapi servers from a configuration file.

    The farm configuration file should contain a list of server configurations,
    each specifying the agent type, directory, and optionally port and other options.

    Example YAML:
        base_port: 3284
        servers:
          - name: worker1
            agent_type: claude
            directory: /path/to/project1
            skip_permissions: true
          - name: worker2
            agent_type: claude
            directory: /path/to/project2
            port: 3290

    Example:
        >>> # cyberian farm start my-farm.yaml
    """
    from cyberian.models import FarmConfig

    # Load farm configuration
    try:
        with open(farm_file, "r") as f:
            farm_data = yaml.safe_load(f)
    except FileNotFoundError:
        typer.echo(f"Error: Farm configuration file '{farm_file}' not found", err=True)
        raise typer.Exit(1)
    except yaml.YAMLError as e:
        typer.echo(f"Error parsing YAML: {e}", err=True)
        raise typer.Exit(1)

    # Validate configuration
    try:
        farm_config = FarmConfig(**farm_data)
    except Exception as e:
        typer.echo(f"Error validating farm configuration: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Starting farm with {len(farm_config.servers)} server(s)...")
    typer.echo(f"Base port: {farm_config.base_port}")

    # Get the directory of the farm config file for resolving relative paths
    farm_file_dir = os.path.dirname(os.path.abspath(farm_file))

    started_servers = []

    # Start each server
    for idx, server_config in enumerate(farm_config.servers):
        # Assign port if not specified
        port = server_config.port if server_config.port is not None else farm_config.base_port + idx

        typer.echo(f"\nStarting server '{server_config.name}':")
        typer.echo(f"  Agent type: {server_config.agent_type}")
        typer.echo(f"  Port: {port}")
        typer.echo(f"  Directory: {server_config.directory}")

        # Change to specified directory
        original_dir = os.getcwd()
        try:
            os.chdir(server_config.directory)
        except FileNotFoundError:
            typer.echo(f"  Error: Directory '{server_config.directory}' not found", err=True)
            continue

        # Copy template directory if specified
        if server_config.template_directory:
            # Resolve template directory relative to farm config file
            template_path = os.path.join(farm_file_dir, server_config.template_directory)

            if not os.path.exists(template_path):
                typer.echo(f"  Warning: Template directory '{template_path}' not found, skipping", err=True)
            elif not os.path.isdir(template_path):
                typer.echo(f"  Warning: Template path '{template_path}' is not a directory, skipping", err=True)
            else:
                typer.echo(f"  Copying template from: {server_config.template_directory}")
                try:
                    # Copy all contents including hidden files/directories
                    for item in os.listdir(template_path):
                        src_path = os.path.join(template_path, item)
                        dst_path = os.path.join(server_config.directory, item)

                        if os.path.isdir(src_path):
                            # Copy directory recursively, overwrite if exists
                            if os.path.exists(dst_path):
                                shutil.rmtree(dst_path)
                            shutil.copytree(src_path, dst_path)
                        else:
                            # Copy file
                            shutil.copy2(src_path, dst_path)
                    typer.echo("  ✓ Template copied successfully")
                except Exception as e:
                    typer.echo(f"  Warning: Error copying template: {e}", err=True)

        # Build command
        cmd = ["agentapi", "server", server_config.agent_type, "--port", str(port)]

        # Add optional flags
        if server_config.allowed_hosts:
            cmd.extend(["--allowed-hosts", server_config.allowed_hosts])

        if server_config.allowed_origins:
            cmd.extend(["--allowed-origins", server_config.allowed_origins])

        # Add agent-specific flags
        agent_flags = []
        if server_config.skip_permissions:
            if server_config.agent_type.lower() == "claude":
                agent_flags.append("--dangerously-skip-permissions")

        if agent_flags:
            cmd.append("--")
            cmd.extend(agent_flags)

        # Start the server process
        try:
            process = subprocess.Popen(cmd)
            typer.echo(f"  ✓ Server started with PID: {process.pid}")
            started_servers.append({
                "name": server_config.name,
                "pid": process.pid,
                "port": port,
                "agent_type": server_config.agent_type
            })
        except Exception as e:
            typer.echo(f"  Error starting server: {e}", err=True)
        finally:
            # Restore original directory
            os.chdir(original_dir)

    # Summary
    typer.echo("\nFarm started successfully!")
    typer.echo(f"Total servers running: {len(started_servers)}")
    typer.echo("\nServer details:")
    for server in started_servers:
        typer.echo(f"  - {server['name']}: PID {server['pid']}, port {server['port']}, agent {server['agent_type']}")


@app.command()
def run(
    workflow_file: Annotated[str, typer.Argument(help="Path to workflow YAML file")],
    host: Annotated[str, typer.Option("--host", "-H", help="Agent API host")] = "localhost",
    port: Annotated[int, typer.Option("--port", "-P", help="Agent API port")] = 3284,
    timeout: Annotated[int, typer.Option("--timeout", "-T", help="Timeout in seconds per task")] = 1800,
    poll_interval: Annotated[float, typer.Option("--poll-interval", help="Status polling interval in seconds")] = 2.0,
    directory: Annotated[
        str | None,
        typer.Option("--dir", "-d", help="Change to this directory before running workflow")
    ] = None,
    agent_type: Annotated[
        str | None,
        typer.Option("--agent-type", "-a", help="Agent type to use (added to template context)")
    ] = None,
    skip_permissions: Annotated[
        bool,
        typer.Option("--skip-permissions", "-s", help="Skip permission checks (added to template context)")
    ] = False,
    resume_from: Annotated[
        str | None,
        typer.Option("--resume-from", "-r", help="Resume workflow from specified task name")
    ] = None,
    agent_lifecycle: Annotated[
        str | None,
        typer.Option("--agent-lifecycle", help="Agent server lifecycle mode: 'reuse' (default, keep server) or 'refresh' (restart between tasks)")
    ] = None,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Increase verbosity (-v for INFO, -vv for DEBUG)")
    ] = 0,
    param: Annotated[
        list[str] | None,
        typer.Option("--param", "-p", help="Parameter in format key=value")
    ] = None,
):
    """Run a workflow from a YAML file.

    Parameters can be provided via --param flags in the format key=value.
    The --agent-type option adds 'agent_type' to the template context.
    The --skip-permissions option adds 'skip_permissions' to the template context.
    The --resume-from option skips tasks until reaching the specified task name.

    Example:
        >>> # cyberian run workflow.yaml --param query="climate change"
        >>> # cyberian run workflow.yaml --dir /my/project --agent-type claude
        >>> # cyberian run workflow.yaml --skip-permissions
        >>> # cyberian run workflow.yaml -v  # verbose output
        >>> # cyberian run workflow.yaml -vv  # debug output
        >>> # cyberian run workflow.yaml --resume-from iterate  # skip to 'iterate' task
        >>> # cyberian run tests/examples/deep-research.yaml -p query="AI" -d ./workspace
    """
    from cyberian.runner import TaskRunner
    from cyberian.models import Task

    # Configure logging based on verbosity
    if verbose == 0:
        log_level = logging.WARNING
    elif verbose == 1:
        log_level = logging.INFO
    else:  # verbose >= 2
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override any existing configuration
    )

    # Suppress httpx INFO messages unless at DEBUG level
    if verbose < 2:
        logging.getLogger("httpx").setLevel(logging.WARNING)

    logger.info(f"Loading workflow from {workflow_file}")

    # Change directory if requested
    if directory:
        logger.info(f"Changing directory to {directory}")
        os.chdir(directory)

    # Load workflow YAML
    with open(workflow_file, 'r') as f:
        workflow_data = yaml.safe_load(f)

    # Parse into Task model
    task = Task(**workflow_data)
    logger.info(f"Loaded workflow: {task.name or 'unnamed'}")
    logger.debug(f"Workflow data: {workflow_data}")

    # Build context from --agent-type and --skip-permissions (can be overridden by --param)
    context: dict[str, Any] = {}
    if agent_type:
        context["agent_type"] = agent_type
        logger.info(f"Using agent type: {agent_type}")
    if skip_permissions:
        context["skip_permissions"] = skip_permissions
        logger.info("Skip permissions enabled")

    # Add --param flags to context (these can override agent_type)
    if param:
        for p in param:
            if "=" not in p:
                typer.echo(f"Error: Invalid param format '{p}'. Use key=value", err=True)
                raise typer.Exit(1)
            key, value_str = p.split("=", 1)
            key = key.strip()
            value_str = value_str.strip()

            # Parse value as YAML to get correct types (int, bool, string, etc.)
            try:
                value = yaml.safe_load(value_str)
            except yaml.YAMLError:
                # If YAML parsing fails, treat as plain string
                value = value_str

            context[key] = value
            logger.info(f"Parameter: {key}={value!r} (type: {type(value).__name__})")

    logger.debug(f"Full context: {context}")

    # Validate required params
    for param_name, param_def in task.params.items():
        if param_def.required and param_name not in context:
            typer.echo(f"Error: Required parameter '{param_name}' not provided", err=True)
            typer.echo(f"Use: --param {param_name}=<value>", err=True)
            raise typer.Exit(1)

    # Run the workflow
    if resume_from:
        logger.info(f"Resuming workflow from task: {resume_from}")
        typer.echo(f"Resuming workflow from: {resume_from}")

    # Determine lifecycle mode: CLI flag > YAML > default "reuse"
    lifecycle_mode = agent_lifecycle or task.agent_lifecycle or "reuse"
    lifecycle_mode = lifecycle_mode.lower()

    # Validate lifecycle mode
    if lifecycle_mode not in ["reuse", "refresh"]:
        typer.echo(f"Error: Invalid agent lifecycle mode '{lifecycle_mode}'. Must be 'reuse' or 'refresh'", err=True)
        raise typer.Exit(1)

    logger.info(f"Initializing TaskRunner (host={host}, port={port}, timeout={timeout}s, poll_interval={poll_interval}s, lifecycle={lifecycle_mode})")
    runner = TaskRunner(
        host=host,
        port=port,
        timeout=timeout,
        poll_interval=poll_interval,
        resume_from=resume_from,
        lifecycle_mode=lifecycle_mode,
        agent_type=agent_type,
        skip_permissions=skip_permissions,
        directory=directory
    )

    typer.echo(f"Starting workflow: {task.name or 'unnamed'}")

    try:
        runner.run_task(task, context)
        typer.echo("Workflow completed successfully!")
        logger.info("Workflow completed successfully")
    finally:
        # Cleanup: stop server if in REFRESH mode
        if lifecycle_mode == "refresh" and runner._server_process:
            logger.info("Cleaning up: stopping agent server")
            runner._stop_server()


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
