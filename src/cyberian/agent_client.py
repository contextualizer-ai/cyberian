"""HTTP client utilities for communicating with agentapi servers.

Simple functions for making HTTP requests to agent API endpoints.
Extracted from cli.py to be reusable by dashboard and other tools.
"""

import json
import time
from typing import Optional

import httpx


def get_agent_status(port: int, host: str = "localhost", timeout: float = 2.0) -> dict:
    """Get status from agentapi server.

    Args:
        port: Port number where the agent server is running
        host: Host address (default: "localhost")
        timeout: Request timeout in seconds (default: 2.0)

    Returns:
        Status dict with keys like: status, timestamp, etc.

    Raises:
        httpx.HTTPError: If the request fails

    Example:
        >>> status = get_agent_status(4800)
        >>> print(f"Agent status: {status['status']}")
    """
    url = f"http://{host}:{port}/status"
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_agent_messages(
    port: int,
    host: str = "localhost",
    last: Optional[int] = None,
    timeout: float = 5.0
) -> list[dict]:
    """Get conversation messages from agentapi server.

    Args:
        port: Port number where the agent server is running
        host: Host address (default: "localhost")
        last: Optional number of recent messages to return
        timeout: Request timeout in seconds (default: 5.0)

    Returns:
        List of message dicts with keys: role, content, timestamp, etc.

    Raises:
        httpx.HTTPError: If the request fails

    Example:
        >>> messages = get_agent_messages(4800, last=10)
        >>> for msg in messages:
        ...     print(f"{msg['role']}: {msg['content']}")
    """
    url = f"http://{host}:{port}/messages"
    params = {}
    if last is not None:
        params['last'] = last

    response = httpx.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data.get('messages', [])


def send_agent_message(
    port: int,
    content: str,
    msg_type: str = "user",
    host: str = "localhost",
    timeout: float = 30.0
) -> dict:
    """Send message to agentapi server.

    Args:
        port: Port number where the agent server is running
        content: Message content to send
        msg_type: Message type (default: "user")
        host: Host address (default: "localhost")
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        Response dict from the server

    Raises:
        httpx.HTTPError: If the request fails

    Example:
        >>> response = send_agent_message(4800, "Hello, agent!")
        >>> print(f"Message sent: {response}")
    """
    url = f"http://{host}:{port}/message"
    payload = {"content": content, "type": msg_type}

    response = httpx.post(
        url,
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def send_message_and_wait(
    port: int,
    content: str,
    host: str = "localhost",
    timeout: int = 60,
    poll_interval: float = 2.0
) -> str:
    """Send message to agent and wait for response.

    This function sends a message and polls the status endpoint until
    the agent finishes processing, then returns the agent's response.

    Args:
        port: Port number where the agent server is running
        content: Message content to send
        host: Host address (default: "localhost")
        timeout: Maximum time to wait in seconds (default: 60)
        poll_interval: Status polling interval in seconds (default: 2.0)

    Returns:
        The agent's response content as a string

    Raises:
        httpx.HTTPError: If any request fails
        TimeoutError: If timeout exceeded waiting for agent
        ValueError: If no agent response found in messages

    Example:
        >>> response = send_message_and_wait(4800, "What is 2+2?")
        >>> print(f"Agent says: {response}")
    """
    # Send the message
    send_agent_message(port, content, host=host, timeout=30.0)

    # Poll status until agent is done processing
    status_url = f"http://{host}:{port}/status"
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(
                f"Timeout exceeded ({timeout}s) waiting for agent to finish processing"
            )

        status_response = httpx.get(status_url, timeout=5.0)
        status_response.raise_for_status()
        status_data = status_response.json()

        # Check if status is stable (not processing/busy)
        agent_status = status_data.get("status", "").lower()
        if agent_status in ["idle", "ready", "stable", "waiting"]:
            break

        time.sleep(poll_interval)

    # Fetch messages and find last agent message
    messages = get_agent_messages(port, host=host, timeout=5.0)

    # Find last message from agent (not from user)
    for msg in reversed(messages):
        role = msg.get("role", "").lower()
        if role in ["agent", "assistant", "system"]:
            return msg.get("content", "")

    raise ValueError("No agent response found in messages")
