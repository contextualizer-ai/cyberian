"""Tests for the command subcommand.

The 'command' command is a convenience wrapper that:
- Starts a new agentapi server (next available port)
- Sends a message synchronously
- Kills the server when done
"""

from unittest.mock import Mock, patch, MagicMock
import socket

from typer.testing import CliRunner

from cyberian.cli import app, find_available_port

runner = CliRunner()


class TestFindAvailablePort:
    """Tests for port discovery functionality."""

    def test_find_available_port_returns_int(self):
        """Test that find_available_port returns an integer."""
        port = find_available_port()
        assert isinstance(port, int)
        assert port > 0

    def test_find_available_port_starts_from_base(self):
        """Test that find_available_port starts from the specified base port."""
        port = find_available_port(base_port=5000)
        assert port >= 5000

    def test_find_available_port_skips_used_ports(self):
        """Test that find_available_port skips ports that are in use."""
        # Bind to a port to make it unavailable
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', 15000))
        sock.listen(1)

        try:
            # Should skip the bound port
            port = find_available_port(base_port=15000)
            assert port > 15000
        finally:
            sock.close()


class TestCommandBasic:
    """Basic tests for the command command."""

    def test_command_starts_server_sends_message_and_stops(self):
        """Test that command starts server, sends message, and stops server."""
        with patch("cyberian.cli.find_available_port") as mock_find_port, \
             patch("cyberian.cli.subprocess.Popen") as mock_popen, \
             patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"), \
             patch("cyberian.cli.subprocess.run") as mock_run:

            mock_find_port.return_value = 4500

            # Mock server process
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Process is running
            mock_popen.return_value = mock_process

            # Mock lsof for stop
            mock_run.return_value = Mock(returncode=0, stdout="12345\n", stderr="")

            # Mock status check for server readiness
            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}

            # Mock messages response
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [
                    {"content": "Hello", "role": "user"},
                    {"content": "Hi there!", "role": "agent"}
                ]
            }

            mock_get.side_effect = [status_ready, status_ready, messages_response]

            # Mock post response
            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "Hello, agent!"])

            assert result.exit_code == 0
            # Server should have been started
            mock_popen.assert_called_once()
            # Message should have been sent
            mock_post.assert_called_once()
            # Server should have been killed
            assert any("kill" in str(call) for call in mock_run.call_args_list)

    def test_command_uses_claude_with_skip_permissions_by_default(self):
        """Test that command uses 'claude -s' (skip permissions) by default."""
        with patch("cyberian.cli.find_available_port") as mock_find_port, \
             patch("cyberian.cli.subprocess.Popen") as mock_popen, \
             patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"), \
             patch("cyberian.cli.subprocess.run") as mock_run:

            mock_find_port.return_value = 4500

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            mock_run.return_value = Mock(returncode=0, stdout="12345\n", stderr="")

            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [{"content": "Response", "role": "agent"}]
            }
            mock_get.side_effect = [status_ready, status_ready, messages_response]

            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "Test"])

            assert result.exit_code == 0
            # Check that the command includes claude and --dangerously-skip-permissions
            popen_call = mock_popen.call_args
            cmd = popen_call[0][0]
            # The command goes through shell, so check the shell command string
            shell_cmd = cmd[2] if len(cmd) > 2 else str(cmd)
            assert "claude" in shell_cmd
            assert "--dangerously-skip-permissions" in shell_cmd

    def test_command_uses_current_directory_by_default(self):
        """Test that command uses current folder by default."""
        with patch("cyberian.cli.find_available_port") as mock_find_port, \
             patch("cyberian.cli.subprocess.Popen") as mock_popen, \
             patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"), \
             patch("cyberian.cli.subprocess.run") as mock_run, \
             patch("cyberian.cli.os.getcwd") as mock_getcwd:

            mock_getcwd.return_value = "/some/project"
            mock_find_port.return_value = 4500

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            mock_run.return_value = Mock(returncode=0, stdout="12345\n", stderr="")

            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [{"content": "Response", "role": "agent"}]
            }
            mock_get.side_effect = [status_ready, status_ready, messages_response]

            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "Test"])

            assert result.exit_code == 0
            # Popen should be called without cwd parameter (uses current dir)
            popen_call = mock_popen.call_args
            # Either no cwd kwarg, or cwd is current directory
            cwd = popen_call.kwargs.get('cwd')
            assert cwd is None or cwd == "/some/project"

    def test_command_returns_agent_response(self):
        """Test that command returns the agent's response."""
        with patch("cyberian.cli.find_available_port") as mock_find_port, \
             patch("cyberian.cli.subprocess.Popen") as mock_popen, \
             patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"), \
             patch("cyberian.cli.subprocess.run") as mock_run:

            mock_find_port.return_value = 4500

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            mock_run.return_value = Mock(returncode=0, stdout="12345\n", stderr="")

            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [
                    {"content": "User query", "role": "user"},
                    {"content": "The answer is 42!", "role": "agent"}
                ]
            }
            mock_get.side_effect = [status_ready, status_ready, messages_response]

            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "What is the meaning of life?"])

            assert result.exit_code == 0
            assert "The answer is 42!" in result.stdout


class TestCommandOptions:
    """Tests for command options."""

    def test_command_with_custom_port(self):
        """Test command with explicit --port option (no server auto-start)."""
        with patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"):

            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [{"content": "Response", "role": "agent"}]
            }
            mock_get.side_effect = [status_ready, messages_response]

            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "Test", "--port", "9000"])

            assert result.exit_code == 0
            # Should connect to the specified port
            call_args = mock_post.call_args
            assert "9000" in call_args[0][0]

    def test_command_no_kill_option(self):
        """Test command with --no-kill option keeps server running."""
        with patch("cyberian.cli.find_available_port") as mock_find_port, \
             patch("cyberian.cli.subprocess.Popen") as mock_popen, \
             patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"), \
             patch("cyberian.cli.subprocess.run") as mock_run:

            mock_find_port.return_value = 4500

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [{"content": "Response", "role": "agent"}]
            }
            mock_get.side_effect = [status_ready, status_ready, messages_response]

            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "Test", "--no-kill"])

            assert result.exit_code == 0
            # Server should NOT have been killed
            kill_calls = [call for call in mock_run.call_args_list
                         if "kill" in str(call)]
            assert len(kill_calls) == 0

    def test_command_with_custom_agent(self):
        """Test command with custom --agent option."""
        with patch("cyberian.cli.find_available_port") as mock_find_port, \
             patch("cyberian.cli.subprocess.Popen") as mock_popen, \
             patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"), \
             patch("cyberian.cli.subprocess.run") as mock_run:

            mock_find_port.return_value = 4500

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            mock_run.return_value = Mock(returncode=0, stdout="12345\n", stderr="")

            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [{"content": "Response", "role": "agent"}]
            }
            mock_get.side_effect = [status_ready, status_ready, messages_response]

            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "Test", "--agent", "aider"])

            assert result.exit_code == 0
            # Check that the command uses aider
            popen_call = mock_popen.call_args
            cmd = popen_call[0][0]
            shell_cmd = cmd[2] if len(cmd) > 2 else str(cmd)
            assert "aider" in shell_cmd

    def test_command_with_timeout(self):
        """Test command with custom --timeout option."""
        with patch("cyberian.cli.find_available_port") as mock_find_port, \
             patch("cyberian.cli.subprocess.Popen") as mock_popen, \
             patch("cyberian.cli.httpx.get") as mock_get, \
             patch("cyberian.cli.httpx.post") as mock_post, \
             patch("cyberian.cli.time.sleep"), \
             patch("cyberian.cli.subprocess.run") as mock_run:

            mock_find_port.return_value = 4500

            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            mock_run.return_value = Mock(returncode=0, stdout="12345\n", stderr="")

            status_ready = Mock(status_code=200)
            status_ready.json.return_value = {"status": "idle"}
            messages_response = Mock(status_code=200)
            messages_response.json.return_value = {
                "messages": [{"content": "Response", "role": "agent"}]
            }
            mock_get.side_effect = [status_ready, status_ready, messages_response]

            mock_post_response = Mock(status_code=200)
            mock_post_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_post_response

            result = runner.invoke(app, ["command", "Test", "--timeout", "300"])

            # Command should complete successfully
            assert result.exit_code == 0
