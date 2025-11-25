"""Tests for additional subcommands (messages, status, server)."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from cyberian.cli import app

runner = CliRunner()


# Tests for messages command (GET /messages)
def test_messages_default_parameters():
    """Test messages command with default parameters."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"content": "Hello", "type": "user"}]}
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages"])

        assert result.exit_code == 0
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://localhost:3284/messages"


def test_messages_custom_host_and_port():
    """Test messages command with custom host and port."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": []}
        mock_get.return_value = mock_response

        result = runner.invoke(
            app,
            ["messages", "--host", "example.com", "--port", "8080"],
        )

        assert result.exit_code == 0
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://example.com:8080/messages"


def test_messages_displays_response():
    """Test that messages response is displayed."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"content": "Hello", "type": "user"}]}
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages"])

        assert result.exit_code == 0
        assert "messages" in result.stdout.lower()


def test_messages_json_format():
    """Test messages command with JSON format (default)."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"content": "Hello", "type": "user"}]}
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages", "--format", "json"])

        assert result.exit_code == 0
        assert "messages" in result.stdout


def test_messages_yaml_format():
    """Test messages command with YAML format."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"content": "Hello", "type": "user"}]}
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages", "--format", "yaml"])

        assert result.exit_code == 0
        assert "messages:" in result.stdout or "- content:" in result.stdout


def test_messages_csv_format():
    """Test messages command with CSV format."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {"content": "Hello", "type": "user"},
                {"content": "Hi there", "type": "assistant"}
            ]
        }
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages", "--format", "csv"])

        assert result.exit_code == 0
        assert "content,type" in result.stdout or "Hello,user" in result.stdout


def test_messages_limit():
    """Test messages command with limit option."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {"content": "Message 1", "type": "user"},
                {"content": "Message 2", "type": "assistant"},
                {"content": "Message 3", "type": "user"},
                {"content": "Message 4", "type": "assistant"},
                {"content": "Message 5", "type": "user"},
            ]
        }
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages", "--last", "2"])

        assert result.exit_code == 0
        # Should only show last 2 messages
        assert "Message 5" in result.stdout
        assert "Message 4" in result.stdout
        assert "Message 1" not in result.stdout


def test_messages_limit_with_yaml():
    """Test messages command with limit and YAML format."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {"content": "Message 1", "type": "user"},
                {"content": "Message 2", "type": "assistant"},
                {"content": "Message 3", "type": "user"},
            ]
        }
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages", "--last", "1", "--format", "yaml"])

        assert result.exit_code == 0
        assert "Message 3" in result.stdout
        assert "Message 1" not in result.stdout


@pytest.mark.parametrize(
    "output_format,expected_content",
    [
        ("json", "messages"),
        ("yaml", "messages:"),
        ("csv", "content,type"),
    ],
)
def test_messages_formats_parametrized(output_format, expected_content):
    """Parametrized test for different output formats."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"content": "Test", "type": "user"}]}
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["messages", "--format", output_format])

        assert result.exit_code == 0


# Tests for status command (GET /status)
def test_status_default_parameters():
    """Test status command with default parameters."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "running", "uptime": 3600}
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://localhost:3284/status"


def test_status_custom_host_and_port():
    """Test status command with custom host and port."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "running"}
        mock_get.return_value = mock_response

        result = runner.invoke(
            app,
            ["status", "--host", "api.example.com", "--port", "9000"],
        )

        assert result.exit_code == 0
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://api.example.com:9000/status"


def test_status_displays_response():
    """Test that status response is displayed."""
    with patch("cyberian.cli.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "running", "uptime": 3600}
        mock_get.return_value = mock_response

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "running" in result.stdout or "status" in result.stdout


# Tests for server command (start agent server)
def test_server_default_parameters():
    """Test server command with default parameters."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start"])

        assert result.exit_code == 0
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert call_args == ["agentapi", "server", "custom", "--port", "3284"]


def test_server_custom_port():
    """Test server command with custom port."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "--port", "8080"])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        assert "8080" in call_args
        assert call_args[0:2] == ["agentapi", "server"]


def test_server_custom_agent():
    """Test server command with custom agent type."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "claude"])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        assert "claude" in call_args
        assert call_args == ["agentapi", "server", "claude", "--port", "3284"]


def test_server_with_allowed_hosts():
    """Test server command with allowed hosts."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "aider", "--allowed-hosts", "localhost,example.com"])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        assert "--allowed-hosts" in call_args
        assert "localhost,example.com" in call_args


@pytest.mark.parametrize(
    "agent,port",
    [
        ("custom", 3284),
        ("claude", 8080),
        ("aider", 9000),
    ],
)
def test_server_parametrized(agent, port):
    """Parametrized test for server command with different agent/port combinations."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", agent, "--port", str(port)])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        assert agent in call_args
        assert str(port) in call_args
        assert call_args[0:2] == ["agentapi", "server"]


# Tests for list-servers command (ps for agentapi)
def test_list_servers_no_servers_running():
    """Test list-servers when no agentapi servers are running."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = runner.invoke(app, ["server", "list"])

        assert result.exit_code == 0
        assert "No agentapi servers found" in result.stdout or result.stdout.strip() == ""
        mock_run.assert_called_once()


def test_list_servers_with_running_servers():
    """Test list-servers when agentapi servers are running."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="USER  PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND\nuser  12345   0.0  0.5  123456  78900 s001  S+    9:00AM   0:01.23 agentapi server claude --host localhost --port 3284\nuser  67890   0.0  0.5  123456  78900 s002  S+    9:00AM   0:01.23 agentapi server claude --host 0.0.0.0 --port 8080\n",
            stderr=""
        )

        result = runner.invoke(app, ["server", "list"])

        assert result.exit_code == 0
        assert "12345" in result.stdout
        assert "67890" in result.stdout
        assert "agentapi" in result.stdout


def test_list_servers_displays_processes():
    """Test that list-servers displays process information."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="12345 agentapi --host localhost --port 3284\n",
            stderr=""
        )

        result = runner.invoke(app, ["server", "list"])

        assert result.exit_code == 0
        assert "3284" in result.stdout or "agentapi" in result.stdout


def test_list_servers_uses_ps_command():
    """Test that list-servers uses ps command to find processes."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="12345 agentapi\n",
            stderr=""
        )

        result = runner.invoke(app, ["server", "list"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        # Should contain ps command
        assert "ps" in str(call_args).lower() or isinstance(call_args, list)


def test_server_with_directory_option():
    """Test server command changes directory when --dir option is provided."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen, \
         patch("cyberian.cli.os.chdir") as mock_chdir:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "--dir", "/tmp/test-dir"])

        assert result.exit_code == 0
        mock_chdir.assert_called_once_with("/tmp/test-dir")
        mock_popen.assert_called_once()


def test_server_without_directory_option():
    """Test server command does not change directory when --dir option is not provided."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen, \
         patch("cyberian.cli.os.chdir") as mock_chdir:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start"])

        assert result.exit_code == 0
        mock_chdir.assert_not_called()
        mock_popen.assert_called_once()


def test_server_with_directory_and_other_options():
    """Test server command with directory option combined with other options."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen, \
         patch("cyberian.cli.os.chdir") as mock_chdir:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "claude", "--port", "8080", "--dir", "/my/project"])

        assert result.exit_code == 0
        mock_chdir.assert_called_once_with("/my/project")
        call_args = mock_popen.call_args[0][0]
        assert "claude" in call_args
        assert "8080" in call_args


def test_server_with_skip_permissions_claude():
    """Test server command with --skip-permissions flag for Claude agent."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "claude", "--skip-permissions"])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        # Should translate to --dangerously-skip-permissions for claude after --
        assert call_args == ["agentapi", "server", "claude", "--port", "3284", "--", "--dangerously-skip-permissions"]


def test_server_with_skip_permissions_other_agent():
    """Test server command with --skip-permissions flag for non-Claude agent."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "aider", "--skip-permissions"])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        # Should not add any agent-specific flags for non-Claude agents
        assert call_args == ["agentapi", "server", "aider", "--port", "3284"]


def test_server_with_name_option():
    """Test server command with --name option sets process name."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "claude", "--name", "my-research-agent"])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        # Should use sh -c with exec -a to set the process name
        assert call_args[0] == "sh"
        assert call_args[1] == "-c"
        assert "exec -a" in call_args[2]
        assert "my-research-agent" in call_args[2]


def test_server_with_name_short_option():
    """Test server command with -n short option for name."""
    with patch("cyberian.cli.subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = runner.invoke(app, ["server", "start", "claude", "-n", "worker1"])

        assert result.exit_code == 0
        call_args = mock_popen.call_args[0][0]
        # Should use exec -a to set the process name
        assert call_args[0] == "sh"
        assert call_args[1] == "-c"
        assert "worker1" in call_args[2]


# Tests for stop command (kill agentapi server)
def test_stop_server_by_pid():
    """Test stop command with PID."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = runner.invoke(app, ["server", "stop", "12345"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "kill" in call_args
        assert "12345" in call_args


def test_stop_server_by_port():
    """Test stop command with port - finds and kills process on that port."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        # First call to lsof to find PID using the port
        # Second call to kill the process
        mock_run.side_effect = [
            Mock(returncode=0, stdout="12345\n", stderr=""),  # lsof output
            Mock(returncode=0, stdout="", stderr="")  # kill output
        ]

        result = runner.invoke(app, ["server", "stop", "--port", "3284"])

        assert result.exit_code == 0
        assert mock_run.call_count == 2
        # First call should be lsof
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "lsof" in first_call_args
        assert "tcp:3284" in first_call_args
        # Second call should be kill
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "kill" in second_call_args
        assert "12345" in second_call_args


def test_stop_server_port_not_found():
    """Test stop command when no process is found on specified port."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        # lsof returns nothing
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="")

        result = runner.invoke(app, ["server", "stop", "--port", "9999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "no process" in result.stdout.lower()


def test_stop_server_invalid_pid():
    """Test stop command with invalid PID."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        # kill returns error
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="No such process")

        result = runner.invoke(app, ["server", "stop", "99999"])

        assert result.exit_code == 1


def test_stop_server_defaults_to_port_3284():
    """Test stop command defaults to port 3284 when no PID or port specified."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        # lsof finds PID on default port 3284
        # Then kill is called
        mock_run.side_effect = [
            Mock(returncode=0, stdout="12345\n", stderr=""),  # lsof output
            Mock(returncode=0, stdout="", stderr="")  # kill output
        ]

        result = runner.invoke(app, ["server", "stop"])

        assert result.exit_code == 0
        assert mock_run.call_count == 2
        # First call should be lsof on port 3284
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "lsof" in first_call_args
        assert "tcp:3284" in first_call_args
        # Second call should be kill
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "kill" in second_call_args
        assert "12345" in second_call_args


def test_stop_server_all():
    """Test stop command with --all flag stops all agentapi servers."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        # First call: ps to find all agentapi processes
        # Then kill calls for each PID
        mock_run.side_effect = [
            Mock(returncode=0, stdout="  PID COMMAND\n12345 agentapi server claude --port 3284\n12346 agentapi server aider --port 8080\n", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),  # kill 12345
            Mock(returncode=0, stdout="", stderr="")   # kill 12346
        ]

        result = runner.invoke(app, ["server", "stop", "--all"])

        assert result.exit_code == 0
        assert mock_run.call_count == 3
        # First call should be ps
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "ps" in first_call_args
        # Second and third calls should be kill
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "kill" in second_call_args
        assert "12345" in second_call_args
        third_call_args = mock_run.call_args_list[2][0][0]
        assert "kill" in third_call_args
        assert "12346" in third_call_args


def test_stop_server_all_no_servers():
    """Test stop command with --all flag when no servers running."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        # ps returns no agentapi processes
        mock_run.return_value = Mock(returncode=0, stdout="  PID COMMAND\n", stderr="")

        result = runner.invoke(app, ["server", "stop", "--all"])

        # Should succeed but report no servers found
        assert result.exit_code == 0
        assert "no" in result.stdout.lower() and "found" in result.stdout.lower()


def test_stop_server_multiple_pids_by_port():
    """Test stop command when multiple processes found on port."""
    with patch("cyberian.cli.subprocess.run") as mock_run:
        # lsof finds multiple PIDs
        mock_run.side_effect = [
            Mock(returncode=0, stdout="12345\n12346\n", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout="", stderr="")
        ]

        result = runner.invoke(app, ["server", "stop", "--port", "3284"])

        assert result.exit_code == 0
        # Should call kill twice (1 lsof + 2 kills)
        assert mock_run.call_count == 3
