"""Tests for the message subcommand."""

import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from cyberian.cli import app

runner = CliRunner()


def test_message_default_parameters():
    """Test message command with default parameters."""
    with patch("cyberian.cli.httpx.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = runner.invoke(app, ["message", "Hello, agent!"])

        assert result.exit_code == 0
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:3284/message"

        payload = json.loads(call_args[1]["content"])
        assert payload["content"] == "Hello, agent!"
        assert payload["type"] == "user"


def test_message_custom_type():
    """Test message command with custom type."""
    with patch("cyberian.cli.httpx.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = runner.invoke(
            app, ["message", "System message", "--type", "system"]
        )

        assert result.exit_code == 0
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]["content"])
        assert payload["content"] == "System message"
        assert payload["type"] == "system"


def test_message_custom_host_and_port():
    """Test message command with custom host and port."""
    with patch("cyberian.cli.httpx.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = runner.invoke(
            app,
            [
                "message",
                "Hello!",
                "--host",
                "example.com",
                "--port",
                "8080",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://example.com:8080/message"


def test_message_displays_response():
    """Test that the response is displayed to the user."""
    with patch("cyberian.cli.httpx.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Agent reply"}
        mock_post.return_value = mock_response

        result = runner.invoke(app, ["message", "Hello"])

        assert result.exit_code == 0
        assert "Agent reply" in result.stdout or "response" in result.stdout


@pytest.mark.parametrize(
    "content,msg_type",
    [
        ("Hello, agent!", "user"),
        ("System initialization", "system"),
        ("Test message", "user"),
    ],
)
def test_message_parametrized(content, msg_type):
    """Parametrized test for different message contents and types."""
    with patch("cyberian.cli.httpx.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = runner.invoke(
            app, ["message", content, "--type", msg_type]
        )

        assert result.exit_code == 0
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]["content"])
        assert payload["content"] == content
        assert payload["type"] == msg_type


def test_message_sync_waits_for_stable_status():
    """Test that sync mode waits for stable status."""
    with patch("cyberian.cli.httpx.post") as mock_post, \
         patch("cyberian.cli.httpx.get") as mock_get, \
         patch("cyberian.cli.time.sleep"):

        # Post response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_post_response

        # Status responses: processing -> processing -> idle
        status_responses = [
            Mock(status_code=200, json=lambda: {"status": "processing"}),
            Mock(status_code=200, json=lambda: {"status": "processing"}),
            Mock(status_code=200, json=lambda: {"status": "idle"}),
        ]

        # Messages response
        messages_response = Mock()
        messages_response.status_code = 200
        messages_response.json.return_value = {
            "messages": [
                {"content": "Hello", "role": "user"},
                {"content": "Hi there!", "role": "agent"}
            ]
        }

        # Setup mock to return status checks then messages
        mock_get.side_effect = status_responses + [messages_response]

        result = runner.invoke(app, ["message", "Hello", "--sync"])

        assert result.exit_code == 0
        # Should display the agent's response
        assert "Hi there!" in result.stdout
        # Should have called status endpoint 3 times
        assert mock_get.call_count == 4  # 3 status + 1 messages


def test_message_sync_returns_last_agent_message():
    """Test that sync mode returns the last agent message."""
    with patch("cyberian.cli.httpx.post") as mock_post, \
         patch("cyberian.cli.httpx.get") as mock_get, \
         patch("cyberian.cli.time.sleep"):

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_post_response

        # Status immediately idle
        status_response = Mock()
        status_response.status_code = 200
        status_response.json.return_value = {"status": "idle"}

        # Messages with multiple agent messages
        messages_response = Mock()
        messages_response.status_code = 200
        messages_response.json.return_value = {
            "messages": [
                {"content": "User message 1", "role": "user"},
                {"content": "Agent response 1", "role": "agent"},
                {"content": "User message 2", "role": "user"},
                {"content": "Agent response 2", "role": "agent"},
            ]
        }

        mock_get.side_effect = [status_response, messages_response]

        result = runner.invoke(app, ["message", "Test", "--sync"])

        assert result.exit_code == 0
        # Should show the last agent message
        assert "Agent response 2" in result.stdout
        assert "Agent response 1" not in result.stdout


def test_message_sync_with_custom_timeout():
    """Test sync mode with custom timeout."""
    with patch("cyberian.cli.httpx.post") as mock_post, \
         patch("cyberian.cli.httpx.get") as mock_get, \
         patch("cyberian.cli.time.sleep"):

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_post_response

        status_response = Mock()
        status_response.status_code = 200
        status_response.json.return_value = {"status": "idle"}

        messages_response = Mock()
        messages_response.status_code = 200
        messages_response.json.return_value = {
            "messages": [
                {"content": "Hello", "role": "user"},
                {"content": "Response", "role": "agent"}
            ]
        }

        mock_get.side_effect = [status_response, messages_response]

        result = runner.invoke(app, ["message", "Test", "--sync", "--timeout", "60"])

        assert result.exit_code == 0
        assert "Response" in result.stdout


def test_message_sync_timeout_exceeded():
    """Test that sync mode fails gracefully on timeout."""
    with patch("cyberian.cli.httpx.post") as mock_post, \
         patch("cyberian.cli.httpx.get") as mock_get, \
         patch("cyberian.cli.time.sleep"), \
         patch("cyberian.cli.time.time") as mock_time:

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_post_response

        # Always return processing status
        status_response = Mock()
        status_response.status_code = 200
        status_response.json.return_value = {"status": "processing"}
        mock_get.return_value = status_response

        # Mock time to simulate timeout
        mock_time.side_effect = [0, 0, 5, 10, 15, 20, 25, 30, 35]

        result = runner.invoke(app, ["message", "Test", "--sync", "--timeout", "30"])

        # Should exit with error or show timeout message
        assert "timeout" in result.stdout.lower() or result.exit_code != 0


def test_message_with_name_resolves_port():
    """Test message command with --name option resolves server name to port."""
    with patch("cyberian.cli.httpx.post") as mock_post, \
         patch("cyberian.cli.subprocess.run") as mock_run:

        # Mock ps output showing a server with a specific name
        mock_run.return_value = Mock(
            returncode=0,
            stdout="USER  PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND\nuser  12345   0.0  0.5  123456  78900 s001  S+    9:00AM   0:01.23 my-research-agent server claude --port 4800 -- --dangerously-skip-permissions\n",
            stderr=""
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = runner.invoke(app, ["message", "Hello", "--name", "my-research-agent"])

        assert result.exit_code == 0
        # Should have called ps to find the server
        mock_run.assert_called_once()
        # Should have sent request to the resolved port
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:4800/message"


def test_message_with_name_short_option():
    """Test message command with -n short option for name."""
    with patch("cyberian.cli.httpx.post") as mock_post, \
         patch("cyberian.cli.subprocess.run") as mock_run:

        # Mock ps output
        mock_run.return_value = Mock(
            returncode=0,
            stdout="USER  PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND\nuser  12345   0.0  0.5  123456  78900 s001  S+    9:00AM   0:01.23 worker1 server claude --port 4801 --\n",
            stderr=""
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = runner.invoke(app, ["message", "Test", "-n", "worker1"])

        assert result.exit_code == 0
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:4801/message"


def test_message_with_name_not_found():
    """Test message command when named server is not found."""
    with patch("cyberian.cli.subprocess.run") as mock_run:

        # Mock ps output showing no matching server
        mock_run.return_value = Mock(
            returncode=0,
            stdout="12345 other-server server claude --port 4800\n",
            stderr=""
        )

        result = runner.invoke(app, ["message", "Hello", "--name", "nonexistent"])

        # Should exit with error
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "no server" in result.stdout.lower()
