"""Tests for the Cyberian Dashboard."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add dashboard backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'backend'))

from main import parse_servers, ServerInfo


class TestDashboardBackend:
    """Test dashboard backend functionality."""

    def test_parse_servers_empty(self):
        """Test parsing when no servers are running."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND\n"
            mock_run.return_value = mock_result

            servers = parse_servers()
            assert servers == []

    def test_parse_servers_single(self):
        """Test parsing a single agentapi server."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = """USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 agentapi server --port 4800"""
            mock_run.return_value = mock_result

            servers = parse_servers()
            assert len(servers) == 1
            assert servers[0].pid == "1234"
            assert servers[0].port == 4800
            assert "agentapi server" in servers[0].command

    def test_parse_servers_multiple(self):
        """Test parsing multiple agentapi servers."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = """USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 agentapi server --port 4800
user    5678  0.0  0.1  123456  7890   s002  S+   10:01AM   0:00.30 agentapi server --port 4801
user    9012  0.0  0.1  123456  7890   s003  S+   10:02AM   0:00.20 test-worker server --port 4802"""
            mock_run.return_value = mock_result

            servers = parse_servers()
            assert len(servers) == 3
            assert servers[0].port == 4800
            assert servers[1].port == 4801
            assert servers[2].port == 4802

    def test_parse_servers_with_names(self):
        """Test parsing servers with custom names."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = """USER    PID   %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
user    1234  0.0  0.1  123456  7890   s001  S+   10:00AM   0:00.50 agentapi server --port 4800 --name worker-1
user    5678  0.0  0.1  123456  7890   s002  S+   10:01AM   0:00.30 research-agent server --port 4801"""
            mock_run.return_value = mock_result

            servers = parse_servers()
            assert len(servers) == 2
            assert servers[0].name == "worker-1"
            assert servers[1].name == "research-agent"  # Extracted from command prefix

    def test_server_info_model(self):
        """Test ServerInfo model validation."""
        server = ServerInfo(
            pid="1234",
            port=4800,
            name="test-server",
            command="agentapi server --port 4800",
            status="running",
            url="http://localhost:4800"
        )
        assert server.pid == "1234"
        assert server.port == 4800
        assert server.name == "test-server"

    @pytest.mark.asyncio
    async def test_check_server_health_success(self):
        """Test checking health of a responsive server."""
        from main import check_server_health

        with patch('httpx.AsyncClient') as mock_client:
            # Create a mock response that's properly awaitable
            mock_response = Mock()
            mock_response.status_code = 200

            # Create async mock for get method
            async def mock_get(*args, **kwargs):
                return mock_response

            # Create async mock for context manager exit
            async def mock_aexit(*args):
                pass

            # Setup the context manager properly
            mock_instance = MagicMock()
            mock_instance.get = mock_get
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = mock_aexit
            mock_client.return_value = mock_instance

            result = await check_server_health(4800)
            assert result.port == 4800
            assert result.status == "healthy"

    @pytest.mark.asyncio
    async def test_check_server_health_failure(self):
        """Test checking health of an unresponsive server."""
        from main import check_server_health

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.get.side_effect = Exception("Connection refused")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await check_server_health(4800)
            assert result.port == 4800
            assert result.status == "unreachable"
            assert "Connection refused" in result.error