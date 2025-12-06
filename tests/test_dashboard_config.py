"""Tests for dashboard_config module."""

from unittest.mock import patch
import pytest
import yaml
from cyberian.dashboard_config import (
    load_dashboard_config,
    save_dashboard_config,
    sync_config_with_running_servers,
    reorder_server_in_config,
)
from cyberian.models import FarmConfig, ServerConfig


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create temporary config directory."""
    config_path = tmp_path / "dashboard.yaml"
    monkeypatch.setattr('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', config_path)
    return config_path


def test_load_dashboard_config_existing(temp_config_dir):
    """Test loading existing dashboard config.

    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     config_path = Path(tmpdir) / "dashboard.yaml"
    ...     config_data = {
    ...         'servers': [
    ...             {'name': 'test', 'agent_type': 'claude', 'port': 4800, 'directory': '/tmp'}
    ...         ]
    ...     }
    ...     with open(config_path, 'w') as f:
    ...         yaml.safe_dump(config_data, f)
    ...     with patch('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', config_path):
    ...         config = load_dashboard_config()
    ...         len(config.servers)
    1
    """
    # Create config file
    config_data = {
        'servers': [
            {'name': 'test-server', 'agent_type': 'claude', 'port': 4800, 'directory': '/tmp'}
        ],
        'base_port': 3284
    }
    with open(temp_config_dir, 'w') as f:
        yaml.safe_dump(config_data, f)

    with patch('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', temp_config_dir):
        config = load_dashboard_config()

    assert len(config.servers) == 1
    assert config.servers[0].name == 'test-server'
    assert config.servers[0].port == 4800
    assert config.base_port == 3284


def test_load_dashboard_config_not_exists(temp_config_dir):
    """Test creating new config when file doesn't exist."""
    with patch('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', temp_config_dir):
        with patch('cyberian.dashboard_config.get_running_servers') as mock_get_servers:
            mock_get_servers.return_value = [
                {'pid': '1234', 'name': 'worker-1', 'port': 4800, 'command': 'agentapi server --port 4800'}
            ]

            with patch('os.getcwd', return_value='/tmp/test'):
                config = load_dashboard_config()

    assert len(config.servers) == 1
    assert config.servers[0].name == 'worker-1'
    assert config.servers[0].port == 4800
    # Verify file was created
    assert temp_config_dir.exists()


def test_load_dashboard_config_corrupt(temp_config_dir):
    """Test handling corrupt config file."""
    # Create corrupt YAML
    with open(temp_config_dir, 'w') as f:
        f.write("invalid: yaml: content: [")

    with patch('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', temp_config_dir):
        with patch('cyberian.dashboard_config.get_running_servers') as mock_get_servers:
            mock_get_servers.return_value = []

            config = load_dashboard_config()

    # Should create new config
    assert config.servers == []


def test_save_dashboard_config(temp_config_dir):
    """Test saving dashboard config atomically."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='test', agent_type='claude', port=4800, directory='/tmp')
        ],
        base_port=3284
    )

    with patch('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', temp_config_dir):
        save_dashboard_config(config)

    assert temp_config_dir.exists()

    # Verify saved content
    with open(temp_config_dir, 'r') as f:
        saved_data = yaml.safe_load(f)

    assert len(saved_data['servers']) == 1
    assert saved_data['servers'][0]['name'] == 'test'
    assert saved_data['base_port'] == 3284


def test_save_dashboard_config_creates_directory(tmp_path, monkeypatch):
    """Test that save creates parent directory if it doesn't exist."""
    config_path = tmp_path / "subdir" / "dashboard.yaml"
    monkeypatch.setattr('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', config_path)

    config = FarmConfig(servers=[])

    with patch('cyberian.dashboard_config.DASHBOARD_CONFIG_PATH', config_path):
        save_dashboard_config(config)

    assert config_path.parent.exists()
    assert config_path.exists()


def test_sync_config_with_running_servers_all_running():
    """Test syncing when all configured servers are still running."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='worker-1', agent_type='claude', port=4800, directory='/tmp'),
            ServerConfig(name='worker-2', agent_type='claude', port=4801, directory='/tmp'),
        ]
    )

    with patch('cyberian.dashboard_config.get_running_servers') as mock_get_servers:
        mock_get_servers.return_value = [
            {'pid': '1234', 'name': 'worker-1', 'port': 4800, 'command': 'worker-1 server --port 4800'},
            {'pid': '5678', 'name': 'worker-2', 'port': 4801, 'command': 'worker-2 server --port 4801'},
        ]

        synced_config = sync_config_with_running_servers(config)

    assert len(synced_config.servers) == 2
    assert synced_config.servers[0].name == 'worker-1'
    assert synced_config.servers[1].name == 'worker-2'


def test_sync_config_with_running_servers_some_stopped():
    """Test syncing when some servers have stopped."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='worker-1', agent_type='claude', port=4800, directory='/tmp'),
            ServerConfig(name='worker-2', agent_type='claude', port=4801, directory='/tmp'),
            ServerConfig(name='worker-3', agent_type='claude', port=4802, directory='/tmp'),
        ]
    )

    with patch('cyberian.dashboard_config.get_running_servers') as mock_get_servers:
        # Only worker-1 and worker-3 are running
        mock_get_servers.return_value = [
            {'pid': '1234', 'name': 'worker-1', 'port': 4800, 'command': 'worker-1 server --port 4800'},
            {'pid': '9012', 'name': 'worker-3', 'port': 4802, 'command': 'worker-3 server --port 4802'},
        ]

        synced_config = sync_config_with_running_servers(config)

    # Should only keep running servers
    assert len(synced_config.servers) == 2
    assert synced_config.servers[0].name == 'worker-1'
    assert synced_config.servers[1].name == 'worker-3'


def test_sync_config_with_running_servers_new_servers():
    """Test syncing when new servers are running."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='worker-1', agent_type='claude', port=4800, directory='/tmp'),
        ]
    )

    with patch('cyberian.dashboard_config.get_running_servers') as mock_get_servers:
        mock_get_servers.return_value = [
            {'pid': '1234', 'name': 'worker-1', 'port': 4800, 'command': 'worker-1 server --port 4800'},
            {'pid': '5678', 'name': 'worker-2', 'port': 4801, 'command': 'worker-2 server --port 4801'},
        ]

        with patch('os.getcwd', return_value='/tmp/test'):
            synced_config = sync_config_with_running_servers(config)

    # Should append new server
    assert len(synced_config.servers) == 2
    assert synced_config.servers[0].name == 'worker-1'
    assert synced_config.servers[1].name == 'worker-2'


def test_sync_config_with_running_servers_error():
    """Test syncing when get_running_servers fails."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='worker-1', agent_type='claude', port=4800, directory='/tmp'),
        ]
    )

    with patch('cyberian.dashboard_config.get_running_servers') as mock_get_servers:
        mock_get_servers.side_effect = RuntimeError("ps command failed")

        synced_config = sync_config_with_running_servers(config)

    # Should return config unchanged
    assert len(synced_config.servers) == 1
    assert synced_config.servers[0].name == 'worker-1'


def test_reorder_server_in_config_move_down():
    """Test moving server down in the list.

    >>> config = FarmConfig(servers=[
    ...     ServerConfig(name='A', agent_type='claude', port=4800, directory='/tmp'),
    ...     ServerConfig(name='B', agent_type='claude', port=4801, directory='/tmp'),
    ...     ServerConfig(name='C', agent_type='claude', port=4802, directory='/tmp'),
    ... ])
    >>> reordered = reorder_server_in_config(config, 0, 2)
    >>> [s.name for s in reordered.servers]
    ['B', 'C', 'A']
    """
    config = FarmConfig(
        servers=[
            ServerConfig(name='A', agent_type='claude', port=4800, directory='/tmp'),
            ServerConfig(name='B', agent_type='claude', port=4801, directory='/tmp'),
            ServerConfig(name='C', agent_type='claude', port=4802, directory='/tmp'),
        ]
    )

    # Move A (index 0) to index 2
    reordered = reorder_server_in_config(config, 0, 2)

    assert [s.name for s in reordered.servers] == ['B', 'C', 'A']


def test_reorder_server_in_config_move_up():
    """Test moving server up in the list."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='A', agent_type='claude', port=4800, directory='/tmp'),
            ServerConfig(name='B', agent_type='claude', port=4801, directory='/tmp'),
            ServerConfig(name='C', agent_type='claude', port=4802, directory='/tmp'),
        ]
    )

    # Move C (index 2) to index 0
    reordered = reorder_server_in_config(config, 2, 0)

    assert [s.name for s in reordered.servers] == ['C', 'A', 'B']


def test_reorder_server_in_config_invalid_old_index():
    """Test error with invalid old_index."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='A', agent_type='claude', port=4800, directory='/tmp'),
        ]
    )

    with pytest.raises(IndexError, match="old_index .* out of range"):
        reorder_server_in_config(config, 5, 0)


def test_reorder_server_in_config_invalid_new_index():
    """Test error with invalid new_index."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='A', agent_type='claude', port=4800, directory='/tmp'),
        ]
    )

    with pytest.raises(IndexError, match="new_index .* out of range"):
        reorder_server_in_config(config, 0, 5)


def test_reorder_server_in_config_preserves_base_port():
    """Test that reordering preserves base_port."""
    config = FarmConfig(
        servers=[
            ServerConfig(name='A', agent_type='claude', port=4800, directory='/tmp'),
            ServerConfig(name='B', agent_type='claude', port=4801, directory='/tmp'),
        ],
        base_port=9999
    )

    reordered = reorder_server_in_config(config, 0, 1)

    assert reordered.base_port == 9999
