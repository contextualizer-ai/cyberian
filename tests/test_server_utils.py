"""Tests for server_utils module."""

from unittest.mock import Mock, patch
import pytest
from cyberian.server_utils import (
    get_running_servers,
    resolve_server_name_to_port,
    find_available_port,
    start_agentapi_server,
    stop_server_by_port,
    stop_server_by_pid,
)


def test_get_running_servers_empty():
    """Test parsing when no servers are running.

    >>> with patch('subprocess.run') as mock_run:
    ...     mock_result = Mock()
    ...     mock_result.returncode = 0
    ...     mock_result.stdout = "USER    PID   COMMAND\\n"
    ...     mock_run.return_value = mock_result
    ...     servers = get_running_servers()
    ...     servers
    []
    """
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND\n"
        mock_run.return_value = mock_result

        servers = get_running_servers()
        assert servers == []


def test_get_running_servers_single():
    """Test parsing a single agentapi server.

    >>> with patch('subprocess.run') as mock_run:
    ...     mock_result = Mock()
    ...     mock_result.returncode = 0
    ...     mock_result.stdout = "USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND\\nuser    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 agentapi server --port 4800"
    ...     mock_run.return_value = mock_result
    ...     servers = get_running_servers()
    ...     len(servers)
    1
    """
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 agentapi server --port 4800"""
        mock_run.return_value = mock_result

        servers = get_running_servers()
        assert len(servers) == 1
        assert servers[0]['pid'] == "1234"
        assert servers[0]['port'] == 4800
        assert "agentapi server" in servers[0]['command']


def test_get_running_servers_multiple():
    """Test parsing multiple agentapi servers."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 agentapi server --port 4800
user    5678  0.0  0.1  123456  7890   s002  S+   10:01AM   0:00.30 agentapi server --port 4801
user    9012  0.0  0.1  123456  7890   s003  S+   10:02AM   0:00.20 test-worker server --port 4802"""
        mock_run.return_value = mock_result

        servers = get_running_servers()
        assert len(servers) == 3
        assert servers[0]['port'] == 4800
        assert servers[1]['port'] == 4801
        assert servers[2]['port'] == 4802


def test_get_running_servers_with_names():
    """Test parsing servers with custom names."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 worker-1 server --port 4800
user    5678  0.0  0.1  123456  7890   s002  S+   10:01AM   0:00.30 research-agent server --port 4801"""
        mock_run.return_value = mock_result

        servers = get_running_servers()
        assert len(servers) == 2
        assert servers[0]['name'] == 'worker-1'
        assert servers[1]['name'] == 'research-agent'


def test_get_running_servers_error():
    """Test handling of ps command errors."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "ps: command failed"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="Error running ps command"):
            get_running_servers()


def test_resolve_server_name_to_port_success():
    """Test resolving server name to port."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 my-worker server --port 4800"""
        mock_run.return_value = mock_result

        port = resolve_server_name_to_port("my-worker")
        assert port == 4800


def test_resolve_server_name_to_port_not_found():
    """Test error when server name is not found."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "USER    PID   COMMAND\n"
        mock_run.return_value = mock_result

        with pytest.raises(ValueError, match="No server found with name 'nonexistent'"):
            resolve_server_name_to_port("nonexistent")


def test_find_available_port_success():
    """Test finding an available port."""
    with patch('cyberian.server_utils.get_running_servers') as mock_get_servers:
        mock_get_servers.return_value = [{'port': 4800}, {'port': 4801}]

        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value.__enter__.return_value = mock_sock

            port = find_available_port(start=4800)
            assert port >= 4800
            assert port < 4900


def test_find_available_port_no_available():
    """Test error when no ports are available."""
    with patch('cyberian.server_utils.get_running_servers') as mock_get_servers:
        mock_get_servers.return_value = []

        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.bind.side_effect = OSError("Address already in use")
            mock_socket.return_value.__enter__.return_value = mock_sock

            with pytest.raises(RuntimeError, match="No available ports in range"):
                find_available_port(start=4800, max_port=4801)


def test_start_agentapi_server_success():
    """Test starting an agentapi server."""
    with patch('os.path.isdir', return_value=True):
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            process = start_agentapi_server(
                agent_type="claude",
                port=4800,
                directory="/tmp/test"
            )

            assert process.pid == 12345
            mock_popen.assert_called_once()


def test_start_agentapi_server_with_name():
    """Test starting an agentapi server with custom name."""
    with patch('os.path.isdir', return_value=True):
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_popen.return_value = mock_process

            start_agentapi_server(
                agent_type="claude",
                port=4800,
                directory="/tmp/test",
                name="my-worker"
            )

            # Verify exec -a was used in shell command
            call_args = mock_popen.call_args
            assert call_args[0][0][0] == "sh"
            assert "exec -a" in call_args[0][0][2]


def test_start_agentapi_server_invalid_directory():
    """Test error when directory doesn't exist."""
    with patch('os.path.isdir', return_value=False):
        with pytest.raises(RuntimeError, match="Directory does not exist"):
            start_agentapi_server(
                agent_type="claude",
                port=4800,
                directory="/nonexistent"
            )


def test_stop_server_by_port_success():
    """Test stopping server by port."""
    with patch('subprocess.run') as mock_run:
        # First call: lsof returns PIDs
        lsof_result = Mock()
        lsof_result.returncode = 0
        lsof_result.stdout = "12345\n67890\n"

        # Second and third calls: kill commands succeed
        kill_result = Mock()
        kill_result.returncode = 0

        mock_run.side_effect = [lsof_result, kill_result, kill_result]

        stop_server_by_port(4800)

        assert mock_run.call_count == 3


def test_stop_server_by_port_not_found():
    """Test error when no process found on port."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="No process found listening on port"):
            stop_server_by_port(4800)


def test_stop_server_by_pid_success():
    """Test stopping server by PID."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        stop_server_by_pid("12345")

        mock_run.assert_called_once_with(
            ["kill", "12345"],
            capture_output=True,
            text=True
        )


def test_stop_server_by_pid_failure():
    """Test error when kill command fails."""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "No such process"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="Failed to kill process"):
            stop_server_by_pid("12345")
