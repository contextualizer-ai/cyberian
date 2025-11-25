"""Task runner for executing recursive task trees."""

import logging
import os
import re
import subprocess
import time
from typing import Any

import httpx
from jinja2 import Template

from cyberian.models import LoopCondition, SuccessCriteria, Task

logger = logging.getLogger(__name__)


class TaskRunner:
    """Executes a recursive task tree by communicating with agentapi.

    The runner:
    - Traverses the task tree depth-first
    - Renders instructions using Jinja2 templates
    - Sends messages to agent and waits for completion
    - Handles looping tasks with loop_until conditions
    - Detects completion and errors via injected status markers

    Example:
        >>> runner = TaskRunner(host="localhost", port=3284)
        >>> task = Task(name="test", instructions="Do {{action}}")
        >>> runner.run_task(task, {"action": "research"})
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3284,
        timeout: int = 300,
        poll_interval: float = 2.0,
        resume_from: str | None = None,
        lifecycle_mode: str = "reuse",
        agent_type: str | None = None,
        skip_permissions: bool = False,
        directory: str | None = None
    ):
        """Initialize the task runner.

        Args:
            host: Agent API host
            port: Agent API port
            timeout: Max seconds to wait for agent per task
            poll_interval: Seconds between status checks (default: 2.0s)
            resume_from: Task name to resume from (skips all tasks before it)
            lifecycle_mode: Agent lifecycle mode - 'reuse' or 'refresh' (default: 'reuse')
            agent_type: Agent type for server management (e.g., 'claude')
            skip_permissions: Whether to skip permissions when starting server
            directory: Working directory for server (if applicable)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.resume_from = resume_from
        self._resume_found = False if resume_from else True  # If no resume, execute from start
        self.base_url = f"http://{host}:{port}"

        # Lifecycle management
        self.lifecycle_mode = lifecycle_mode
        self.agent_type = agent_type
        self.skip_permissions = skip_permissions
        self.directory = directory
        self._server_process: subprocess.Popen[bytes] | None = None  # Track the subprocess.Popen instance

    def _start_server(self) -> None:
        """Start an agentapi server process.

        Raises:
            RuntimeError: If agent_type is not specified or server fails to start
        """
        if not self.agent_type:
            raise RuntimeError(
                "Cannot start server: agent_type not specified. "
                "Provide --agent-type when using --agent-lifecycle refresh"
            )

        logger.info(f"Starting agentapi server ({self.agent_type}) on port {self.port}")

        # Check for and kill any existing server on this port
        self._kill_server_on_port()

        # Change to directory if specified
        original_dir = None
        if self.directory:
            original_dir = os.getcwd()
            os.chdir(self.directory)
            logger.debug(f"Changed directory to: {self.directory}")

        # Build command
        cmd = ["agentapi", "server", self.agent_type, "--port", str(self.port)]

        # Add agent-specific flags if skip_permissions
        if self.skip_permissions:
            if self.agent_type.lower() == "claude":
                cmd.extend(["--", "--dangerously-skip-permissions"])
                logger.debug("Added --dangerously-skip-permissions flag for Claude agent")

        # Start the process
        try:
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Server started with PID: {self._server_process.pid}")

            # Wait for server to be ready to accept messages
            self._wait_for_server_ready()

        finally:
            # Restore original directory
            if original_dir:
                os.chdir(original_dir)
                logger.debug(f"Restored directory to: {original_dir}")

    def _stop_server(self) -> None:
        """Stop the running agentapi server process."""
        if not self._server_process:
            logger.debug("No server process to stop")
            return

        logger.info(f"Stopping server with PID: {self._server_process.pid}")

        try:
            self._server_process.terminate()
            # Wait up to 5 seconds for graceful shutdown
            self._server_process.wait(timeout=5)
            logger.info("Server stopped successfully")
        except subprocess.TimeoutExpired:
            logger.warning("Server did not terminate gracefully, forcing kill")
            self._server_process.kill()
            self._server_process.wait()
            logger.info("Server killed")
        finally:
            self._server_process = None

    def _kill_server_on_port(self) -> None:
        """Kill any existing agentapi server running on the configured port."""
        try:
            # Use lsof to find process using the port
            result = subprocess.run(
                ["lsof", "-ti", f":{self.port}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        pid_int = int(pid)
                        logger.info(f"Found existing server on port {self.port} (PID: {pid_int}), killing it")
                        os.kill(pid_int, 9)  # SIGKILL
                        time.sleep(0.5)  # Brief wait for cleanup
                    except (ValueError, ProcessLookupError) as e:
                        logger.debug(f"Could not kill PID {pid}: {e}")
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout checking for existing server on port {self.port}")
        except FileNotFoundError:
            # lsof not available, skip check
            logger.debug("lsof command not available, skipping port check")
        except Exception as e:
            logger.debug(f"Error checking for existing server: {e}")

    def _wait_for_server_ready(self, max_wait: int = 30) -> None:
        """Wait for the server to be ready to accept messages.

        This waits for the HTTP endpoint to respond, then gives the agent
        additional time to fully initialize before accepting messages.

        Args:
            max_wait: Maximum seconds to wait for server to be ready

        Raises:
            TimeoutError: If server doesn't become ready within max_wait seconds
        """
        logger.debug(f"Waiting for server to be ready (max {max_wait}s)")
        start_time = time.time()

        # Phase 1: Wait for HTTP endpoint to respond
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(
                    f"Server did not become ready within {max_wait}s"
                )

            try:
                response = httpx.get(f"{self.base_url}/status", timeout=1.0)
                if response.status_code == 200:
                    logger.debug(f"Server HTTP endpoint responding after {elapsed:.1f}s")
                    break
            except (httpx.ConnectError, httpx.TimeoutException):
                # Server not ready yet, continue waiting
                pass

            time.sleep(0.5)

        # Phase 2: Additional wait for agent initialization
        # After the HTTP endpoint responds, the agent needs time to fully initialize
        # before it can accept messages. Poll with increasing delays.
        logger.debug("Waiting for agent to fully initialize...")
        max_init_wait = 10  # Wait up to 10 seconds for initialization
        init_start = time.time()

        while True:
            init_elapsed = time.time() - init_start
            if init_elapsed > max_init_wait:
                logger.warning(f"Agent initialization timeout after {init_elapsed:.1f}s, proceeding anyway")
                return

            try:
                # Check status to see if agent is in a good state
                response = httpx.get(f"{self.base_url}/status", timeout=1.0)
                if response.status_code == 200:
                    status_data = response.json()
                    agent_status = status_data.get("status", "").lower()

                    # After a minimum wait time, accept stable/idle/ready/waiting states
                    if init_elapsed >= 2.0 and agent_status in ["stable", "idle", "ready", "waiting"]:
                        total_elapsed = time.time() - start_time
                        logger.info(f"Server ready (status: {agent_status}) after {total_elapsed:.1f}s")
                        return

            except Exception as e:
                logger.debug(f"Error during initialization check: {e}")

            time.sleep(1.0)  # Check every second

    def run_task(
        self,
        task: Task,
        context: dict[str, Any],
        task_name_override: str | None = None,
        parent_system_instructions: str | None = None
    ) -> None:
        """Execute a task and all its subtasks.

        Args:
            task: The task to execute
            context: Template variables (params) for Jinja2
            task_name_override: Override for task name (used for subtasks from dict keys)
            parent_system_instructions: System instructions inherited from parent tasks

        Raises:
            RuntimeError: If task execution fails or returns ERROR status
            TimeoutError: If agent doesn't respond within timeout
        """
        # Use override name if provided (for subtasks), otherwise use task.name
        task_name = task_name_override or task.name or "unnamed"

        # Inherit or override system_instructions
        current_system_instructions = task.system_instructions or parent_system_instructions
        if current_system_instructions:
            logger.debug(f"Task '{task_name}' using system instructions: {current_system_instructions[:50]}...")

        # Check if this is the resume point
        if self.resume_from and not self._resume_found:
            if task_name == self.resume_from:
                logger.info(f"Found resume point: {task_name}")
                self._resume_found = True
            else:
                logger.info(f"Skipping task: {task_name} (resuming from {self.resume_from})")
                # Still need to check subtasks for the resume point
                for subtask_name, subtask in task.subtasks.items():
                    self.run_task(subtask, context, task_name_override=subtask_name,
                                 parent_system_instructions=current_system_instructions)
                return

        logger.info(f"Starting task: {task_name}")
        logger.debug(f"Task context: {context}")

        # Handle agent lifecycle for tasks with instructions
        if task.instructions and self.lifecycle_mode == "refresh":
            logger.info(f"REFRESH mode: Restarting agent server for task '{task_name}'")
            # Stop existing server if any
            if self._server_process:
                self._stop_server()
            # Start fresh server
            self._start_server()

        # Execute this task's provider call or instructions
        if task.provider_call:
            logger.info(f"Task '{task_name}' is a provider call task")
            self._run_provider_task(task, context)
        elif task.instructions:
            if task.loop_until:
                logger.info(f"Task '{task_name}' is a looping task with condition: {task.loop_until.status}")
                self._run_looping_task(task, context, current_system_instructions)
            else:
                logger.info(f"Task '{task_name}' is a single-run task")
                self._run_single_task(task, context, current_system_instructions)
        else:
            logger.debug(f"Task '{task_name}' has no instructions or provider call, skipping execution")

        # Execute subtasks depth-first, in order
        if task.subtasks:
            logger.info(f"Task '{task_name}' has {len(task.subtasks)} subtask(s)")
        for subtask_name, subtask in task.subtasks.items():
            logger.info(f"Executing subtask: {subtask_name}")
            self.run_task(subtask, context, task_name_override=subtask_name,
                         parent_system_instructions=current_system_instructions)

        logger.info(f"Completed task: {task_name}")

    def _run_single_task(
        self,
        task: Task,
        context: dict[str, Any],
        system_instructions: str | None = None
    ) -> None:
        """Run a non-looping task once, with optional retries on validation failure.

        Args:
            task: Task to execute
            context: Template context
            system_instructions: System-level instructions to inject
        """
        assert task.instructions is not None, "Task must have instructions"

        max_attempts = 1
        if task.success_criteria and task.success_criteria.max_retries > 0:
            max_attempts = task.success_criteria.max_retries + 1

        last_error = None

        for attempt in range(max_attempts):
            if attempt > 0 and task.success_criteria:
                logger.info(f"Retry attempt {attempt}/{task.success_criteria.max_retries}")

            # Render template
            instructions = self._render_instructions(task.instructions, context)

            # If this is a retry, prepend retry message with error details
            if attempt > 0 and task.success_criteria and task.success_criteria.retry_message:
                retry_context = {**context, "error": last_error or "Unknown error"}
                retry_msg = self._render_instructions(task.success_criteria.retry_message, retry_context)
                instructions = f"{retry_msg}\n\n{instructions}"
                logger.debug(f"Injected retry message: {retry_msg[:100]}...")

            # Inject system instructions if present
            if system_instructions:
                rendered_system = self._render_instructions(system_instructions, context)
                instructions = f"{rendered_system}\n\n{instructions}"
                logger.debug("Injected system instructions into prompt")

            # Inject completion status marker
            full_instructions = self._inject_completion_marker(instructions)

            # Send message and wait
            agent_response = self._send_and_wait(full_instructions)

            # Check completion status
            self._check_completion_status(agent_response)

            # Check success criteria if present
            if task.success_criteria:
                success, error_msg = self._check_success_criteria(task.success_criteria, context)
                if success:
                    logger.info("Success criteria passed")
                    return  # Success!
                else:
                    last_error = error_msg
                    if attempt < max_attempts - 1:
                        logger.warning(f"Success criteria failed: {error_msg}. Retrying...")
                    else:
                        # No more retries left
                        logger.error(f"Success criteria failed after {max_attempts} attempt(s): {error_msg}")
                        raise RuntimeError(f"Success criteria validation failed: {error_msg}")

    def _run_looping_task(
        self,
        task: Task,
        context: dict[str, Any],
        system_instructions: str | None = None
    ) -> None:
        """Run a task repeatedly until loop condition is met, with optional retries on validation failure.

        Args:
            task: Task with loop_until condition
            context: Template context
            system_instructions: System-level instructions to inject
        """
        assert task.instructions is not None, "Task must have instructions"
        assert task.loop_until is not None, "Task must have loop_until condition"

        max_attempts = 1
        if task.success_criteria and task.success_criteria.max_retries > 0:
            max_attempts = task.success_criteria.max_retries + 1

        last_error = None

        for attempt in range(max_attempts):
            if attempt > 0 and task.success_criteria:
                logger.info(f"Retry attempt {attempt}/{task.success_criteria.max_retries} for looping task")

            iteration = 0
            while True:
                iteration += 1
                logger.info(f"Loop iteration {iteration} for task '{task.name or 'unnamed'}'")

                # Render template
                instructions = self._render_instructions(task.instructions, context)
                logger.debug(f"Rendered instructions (iteration {iteration}): {instructions[:100]}...")

                # If this is a retry (attempt > 0) and first iteration, prepend retry message
                if attempt > 0 and iteration == 1 and task.success_criteria and task.success_criteria.retry_message:
                    retry_context = {**context, "error": last_error or "Unknown error"}
                    retry_msg = self._render_instructions(task.success_criteria.retry_message, retry_context)
                    instructions = f"{retry_msg}\n\n{instructions}"
                    logger.debug(f"Injected retry message: {retry_msg[:100]}...")

                # Inject system instructions if present
                if system_instructions:
                    rendered_system = self._render_instructions(system_instructions, context)
                    instructions = f"{rendered_system}\n\n{instructions}"
                    logger.debug(f"Injected system instructions into prompt (iteration {iteration})")

                # Inject loop condition message AND completion marker
                full_instructions = self._inject_loop_condition(
                    instructions, task.loop_until
                )
                full_instructions = self._inject_completion_marker(full_instructions)

                # Send and wait
                logger.info(f"Sending message to agent (iteration {iteration})")
                agent_response = self._send_and_wait(full_instructions)

                # Check for error first
                self._check_completion_status(agent_response)

                # Check if loop should exit
                if self._check_loop_status(agent_response, task.loop_until.status):
                    logger.info(f"Loop condition '{task.loop_until.status}' met after {iteration} iteration(s)")
                    break
                else:
                    logger.info(f"Loop condition not met, continuing (iteration {iteration})")

            # Check success criteria after loop completes
            if task.success_criteria:
                success, error_msg = self._check_success_criteria(task.success_criteria, context)
                if success:
                    logger.info("Success criteria passed")
                    return  # Success!
                else:
                    last_error = error_msg
                    if attempt < max_attempts - 1:
                        logger.warning(f"Success criteria failed: {error_msg}. Retrying entire looping task...")
                    else:
                        # No more retries left
                        logger.error(f"Success criteria failed after {max_attempts} attempt(s): {error_msg}")
                        raise RuntimeError(f"Success criteria validation failed: {error_msg}")

    def _run_provider_task(self, task: Task, context: dict[str, Any]) -> None:
        """Execute a task using a provider call instead of an agent.

        Args:
            task: Task with provider_call configuration
            context: Template context

        Raises:
            RuntimeError: If provider call fails
        """
        assert task.provider_call is not None, "Task must have provider_call"

        provider_call = task.provider_call

        # Render parameters with Jinja2 templates
        rendered_params: dict[str, Any] = {}
        for key, value in provider_call.params.items():
            if isinstance(value, str):
                rendered_params[key] = self._render_instructions(value, context)
            elif isinstance(value, list):
                # Render list items that are strings
                rendered_params[key] = [
                    self._render_instructions(item, context) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                rendered_params[key] = value

        logger.debug(f"Rendered provider params: {rendered_params}")

        # Render output_file if present
        output_file = None
        if provider_call.output_file:
            output_file = self._render_instructions(provider_call.output_file, context)
            logger.debug(f"Output file: {output_file}")

        # Get provider
        from cyberian.providers import get_provider

        try:
            provider = get_provider(provider_call.provider)
            logger.info(f"Using provider: {provider_call.provider}, method: {provider_call.method}")
        except ValueError as e:
            logger.error(f"Provider error: {e}")
            raise RuntimeError(f"Provider not found: {e}") from e

        # Execute provider method
        try:
            result = provider.execute(provider_call.method, rendered_params)
            logger.info(f"Provider call successful, result length: {len(result)} chars")

            # Write output file if specified
            if output_file:
                import os
                os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
                with open(output_file, "w") as f:
                    f.write(result)
                logger.info(f"Wrote results to: {output_file}")
            else:
                # Log a preview of the result
                logger.debug(f"Provider result preview: {result[:200]}...")

        except Exception as e:
            logger.error(f"Provider call failed: {e}")
            raise RuntimeError(f"Provider '{provider_call.provider}' call failed: {e}") from e

        # Check success criteria if present (for provider tasks too)
        if task.success_criteria:
            success, error_msg = self._check_success_criteria(task.success_criteria, context)
            if success:
                logger.info("Success criteria passed")
            else:
                logger.error(f"Success criteria failed: {error_msg}")
                raise RuntimeError(f"Success criteria validation failed: {error_msg}")

    def _render_instructions(self, instructions: str, context: dict[str, Any]) -> str:
        """Render Jinja2 template with context variables.

        Args:
            instructions: Template string with {{variable}} placeholders
            context: Dictionary of variable values

        Returns:
            Rendered instructions string
        """
        template = Template(instructions)
        return template.render(**context)

    def _inject_completion_marker(self, instructions: str) -> str:
        """Inject completion status requirement at end of instructions.

        Args:
            instructions: Original instructions

        Returns:
            Instructions with completion marker appended
        """
        marker = (
            "\n\n"
            "IMPORTANT: When you have completed this task, print the completion "
            "status as the final message in this format:\n"
            "COMPLETION_STATUS: COMPLETE\n"
            "If you encounter an error that prevents completion, print:\n"
            "COMPLETION_STATUS: ERROR"
        )
        return instructions + marker

    def _inject_loop_condition(self, instructions: str, loop_until: LoopCondition) -> str:
        """Inject loop termination message into instructions.

        Args:
            instructions: Original instructions
            loop_until: Loop condition with status and message

        Returns:
            Instructions with loop message appended
        """
        loop_msg = f"\n\n{loop_until.message}"
        return instructions + loop_msg

    def _send_and_wait(self, content: str) -> str:
        """Send message to agent and wait for stable status, return last agent message.

        Args:
            content: Message content to send

        Returns:
            Last agent response message

        Raises:
            TimeoutError: If agent doesn't respond within timeout
            RuntimeError: If no agent response found
        """
        # Send message
        logger.debug(f"Sending message to {self.base_url}/message")
        response = httpx.post(
            f"{self.base_url}/message",
            json={"content": content, "type": "user"},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info("Message sent successfully, waiting for agent to complete")

        # Wait for stable status
        start_time = time.time()
        last_status = None
        status_change_count = 0
        while True:
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                logger.error(f"Timeout exceeded: {elapsed:.1f}s > {self.timeout}s")
                raise TimeoutError(
                    f"Agent did not complete within {self.timeout}s"
                )

            status_response = httpx.get(f"{self.base_url}/status")
            status_response.raise_for_status()
            status_data = status_response.json()

            agent_status = status_data.get("status", "").lower()

            # Log status changes
            if agent_status != last_status:
                status_change_count += 1
                logger.info(f"Agent status changed to: {agent_status} (elapsed: {elapsed:.1f}s)")
                last_status = agent_status

            if agent_status in ["idle", "ready", "stable", "waiting"]:
                logger.info(f"Agent reached stable status: {agent_status} after {elapsed:.1f}s")
                break

            time.sleep(self.poll_interval)

        # Get last agent message
        logger.debug("Fetching agent messages")
        messages_response = httpx.get(f"{self.base_url}/messages")
        messages_response.raise_for_status()
        messages_data = messages_response.json()

        messages_list = messages_data.get("messages", [])
        logger.debug(f"Retrieved {len(messages_list)} total messages")

        # Find last agent message
        for msg in reversed(messages_list):
            role = msg.get("role", "").lower()
            if role in ["agent", "assistant", "system"]:
                response_preview = msg.get("content", "")[:200]
                logger.info(f"Received agent response (preview): {response_preview}...")
                return msg.get("content", "")

        logger.error("No agent response found in messages")
        raise RuntimeError("No agent response found")

    def _check_completion_status(self, agent_response: str) -> None:
        """Check for COMPLETION_STATUS marker and raise if ERROR.

        Args:
            agent_response: Agent's response message

        Raises:
            RuntimeError: If COMPLETION_STATUS: ERROR is found
        """
        # Look for "COMPLETION_STATUS: ERROR" or "COMPLETION_STATUS:ERROR"
        pattern = r'COMPLETION_STATUS:\s*(COMPLETE|ERROR)'
        match = re.search(pattern, agent_response, re.IGNORECASE)

        if match:
            status = match.group(1).upper()
            if status == "ERROR":
                raise RuntimeError(
                    "Task execution failed. Agent reported: COMPLETION_STATUS: ERROR"
                )
        # If no match found, that's potentially a problem but we'll be lenient
        # (agent might have completed but not printed the marker)

    def _check_success_criteria(self, success_criteria: SuccessCriteria, context: dict[str, Any]) -> tuple[bool, str | None]:
        """Execute success criteria validation code.

        Args:
            success_criteria: SuccessCriteria with Python code to execute
            context: Template context for rendering variables

        Returns:
            Tuple of (success: bool, error_message: str | None)
            - (True, None) if validation passes
            - (False, error_msg) if validation fails
        """
        logger.info("Checking success criteria")

        # Render the Python code with template context
        rendered_code = self._render_instructions(success_criteria.python, context)
        logger.debug(f"Rendered success criteria code: {rendered_code[:100]}...")

        # Create a restricted namespace for code execution
        namespace = {
            "__builtins__": {
                "len": len,
                "open": open,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "True": True,
                "False": False,
                "None": None,
            }
        }

        try:
            # Execute the Python code
            exec(rendered_code, namespace)

            # The code should set a 'result' variable
            result = namespace.get("result")

            if result is None:
                error_msg = (
                    "Success criteria code did not set 'result' variable. "
                    "Code must set result = True or result = False"
                )
                logger.error(error_msg)
                return (False, error_msg)

            if not isinstance(result, bool):
                error_msg = f"Success criteria result must be bool, got {type(result).__name__}"
                logger.error(error_msg)
                return (False, error_msg)

            if not result:
                error_msg = "Success criteria validation failed: result = False"
                logger.warning(error_msg)
                return (False, error_msg)

            logger.info("Success criteria passed")
            return (True, None)

        except Exception as e:
            error_msg = f"Error executing success criteria: {e}"
            logger.error(error_msg)
            return (False, error_msg)

    def _check_loop_status(self, agent_response: str, expected_status: str) -> bool:
        """Check if the expected loop termination status appears in response.

        Args:
            agent_response: Agent's response message
            expected_status: Status string to look for (e.g., "NO_MORE_RESEARCH")

        Returns:
            True if status found (should exit loop), False otherwise
        """
        # Case-insensitive search for the status string
        # We look for it as a standalone word to avoid partial matches
        pattern = r'\b' + re.escape(expected_status) + r'\b'
        return bool(re.search(pattern, agent_response, re.IGNORECASE))
