"""Dashboard configuration management.

Functions for loading, saving, and managing the persistent dashboard configuration
stored in ~/.cyberian/dashboard.yaml using the FarmConfig model.
"""

import os
import tempfile
from pathlib import Path

import yaml

from cyberian.models import FarmConfig, ServerConfig
from cyberian.server_utils import get_running_servers


# Path to dashboard configuration file
DASHBOARD_CONFIG_PATH = Path.home() / ".cyberian" / "dashboard.yaml"


def load_dashboard_config() -> FarmConfig:
    """Load dashboard configuration from ~/.cyberian/dashboard.yaml.

    If the file doesn't exist, creates it from currently running servers.

    Returns:
        FarmConfig object with server configurations

    Example:
        >>> config = load_dashboard_config()
        >>> for server in config.servers:
        ...     print(f"{server.name} on port {server.port}")
    """
    if DASHBOARD_CONFIG_PATH.exists():
        try:
            with open(DASHBOARD_CONFIG_PATH, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    return FarmConfig(**data)
        except Exception as e:
            # If config is corrupt, fall through to create new one
            print(f"Warning: Could not load config: {e}. Creating new config.")

    # Create config from running servers
    try:
        running_servers = get_running_servers()
    except Exception:
        running_servers = []

    # Build ServerConfig objects from running servers
    servers = []
    for ps_info in running_servers:
        server_config = ServerConfig(
            name=ps_info.get('name') or f"port-{ps_info['port']}",
            agent_type="claude",  # Default, can't determine from ps
            port=ps_info['port'],
            directory=os.getcwd()  # Default to current directory
        )
        servers.append(server_config)

    config = FarmConfig(servers=servers)

    # Save the newly created config
    save_dashboard_config(config)

    return config


def save_dashboard_config(config: FarmConfig) -> None:
    """Save FarmConfig to ~/.cyberian/dashboard.yaml atomically.

    Uses temp file + rename for atomic writes to avoid corruption.

    Args:
        config: FarmConfig object to save

    Example:
        >>> config = FarmConfig(servers=[...])
        >>> save_dashboard_config(config)
    """
    # Ensure parent directory exists
    DASHBOARD_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict and write to temp file
    config_dict = config.model_dump(exclude_none=True)

    # Write to temporary file first
    fd, temp_path = tempfile.mkstemp(
        dir=DASHBOARD_CONFIG_PATH.parent,
        prefix='.dashboard_',
        suffix='.yaml.tmp'
    )

    try:
        with os.fdopen(fd, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)

        # Atomic rename
        os.rename(temp_path, DASHBOARD_CONFIG_PATH)
    except:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def sync_config_with_running_servers(config: FarmConfig) -> FarmConfig:
    """Merge config with currently running servers.

    Strategy:
    - Keep servers in config order if they're still running
    - Append new running servers not in config
    - Remove stopped servers from config

    Args:
        config: Current FarmConfig

    Returns:
        Updated FarmConfig with synced servers

    Example:
        >>> config = load_dashboard_config()
        >>> config = sync_config_with_running_servers(config)
        >>> save_dashboard_config(config)
    """
    try:
        running_servers = get_running_servers()
    except Exception:
        # If can't get running servers, return config unchanged
        return config

    # Build set of running ports for fast lookup
    running_ports = {s['port'] for s in running_servers}

    # Keep only servers that are still running
    active_servers = []
    for server_cfg in config.servers:
        if server_cfg.port in running_ports:
            active_servers.append(server_cfg)

    # Find new servers not in config
    configured_ports = {s.port for s in active_servers}
    new_servers = []

    for ps_info in running_servers:
        if ps_info['port'] not in configured_ports:
            # New server - add to end
            new_server = ServerConfig(
                name=ps_info.get('name') or f"port-{ps_info['port']}",
                agent_type="claude",  # Default
                port=ps_info['port'],
                directory=os.getcwd()  # Default
            )
            new_servers.append(new_server)

    # Combine: active servers in original order + new servers at end
    all_servers = active_servers + new_servers

    return FarmConfig(servers=all_servers, base_port=config.base_port)


def reorder_server_in_config(
    config: FarmConfig,
    old_index: int,
    new_index: int
) -> FarmConfig:
    """Move server from old_index to new_index.

    Uses Python list.insert() semantics - removes from old_index,
    inserts at new_index, everything shifts right.

    Args:
        config: Current FarmConfig
        old_index: Current index of server (0-based)
        new_index: Target index (0-based)

    Returns:
        New FarmConfig with reordered servers

    Raises:
        IndexError: If indices are out of range

    Example:
        >>> config = load_dashboard_config()
        >>> # Move server from position 2 to position 0
        >>> config = reorder_server_in_config(config, 2, 0)
        >>> save_dashboard_config(config)
    """
    servers = list(config.servers)

    # Validate indices
    if old_index < 0 or old_index >= len(servers):
        raise IndexError(f"old_index {old_index} out of range (0-{len(servers)-1})")
    if new_index < 0 or new_index >= len(servers):
        raise IndexError(f"new_index {new_index} out of range (0-{len(servers)-1})")

    # Remove from old position
    server = servers.pop(old_index)

    # Insert at new position
    servers.insert(new_index, server)

    return FarmConfig(servers=servers, base_port=config.base_port)
