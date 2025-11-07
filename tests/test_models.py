"""Tests for models."""

import pytest

from cyberian.models import FarmConfig, ParamDefinition, ServerConfig, Task


def test_param_definition_with_examples():
    """Test ParamDefinition with examples field."""
    param = ParamDefinition(
        range="string",
        required=True,
        examples=["example1.pdf", "example2.pdf"]
    )

    assert param.range == "string"
    assert param.required is True
    assert param.examples == ["example1.pdf", "example2.pdf"]


def test_param_definition_without_examples():
    """Test ParamDefinition without examples (should default to empty list)."""
    param = ParamDefinition(
        range="integer",
        required=False
    )

    assert param.range == "integer"
    assert param.required is False
    assert param.examples == []


def test_param_definition_with_mixed_type_examples():
    """Test ParamDefinition with different types of examples."""
    # String examples
    param_str = ParamDefinition(range="string", examples=["foo", "bar"])
    assert param_str.examples == ["foo", "bar"]

    # Integer examples
    param_int = ParamDefinition(range="integer", examples=[1, 2, 3])
    assert param_int.examples == [1, 2, 3]

    # Mixed examples (though not recommended in practice)
    param_mixed = ParamDefinition(range="any", examples=["foo", 42, True])
    assert param_mixed.examples == ["foo", 42, True]


def test_task_with_params_including_examples():
    """Test Task with params that include examples."""
    task = Task(
        name="test-task",
        params={
            "url": ParamDefinition(
                range="string",
                required=True,
                examples=["https://example.com/doc.pdf"]
            ),
            "count": ParamDefinition(
                range="integer",
                required=False,
                examples=[10, 20, 30]
            )
        }
    )

    assert task.name == "test-task"
    assert "url" in task.params
    assert task.params["url"].examples == ["https://example.com/doc.pdf"]
    assert task.params["count"].examples == [10, 20, 30]


def test_server_config_minimal():
    """Test ServerConfig with minimal required fields."""
    server = ServerConfig(
        name="test-server",
        directory="/tmp/test"
    )

    assert server.name == "test-server"
    assert server.agent_type == "custom"  # default
    assert server.port is None  # will be auto-assigned
    assert server.directory == "/tmp/test"
    assert server.skip_permissions is False
    assert server.allowed_hosts is None
    assert server.allowed_origins is None
    assert server.template_directory is None


def test_server_config_full():
    """Test ServerConfig with all fields specified."""
    server = ServerConfig(
        name="claude-worker",
        agent_type="claude",
        port=4000,
        directory="/workspace",
        skip_permissions=True,
        allowed_hosts="localhost,127.0.0.1",
        allowed_origins="http://localhost:3000",
        template_directory=".claude"
    )

    assert server.name == "claude-worker"
    assert server.agent_type == "claude"
    assert server.port == 4000
    assert server.directory == "/workspace"
    assert server.skip_permissions is True
    assert server.allowed_hosts == "localhost,127.0.0.1"
    assert server.allowed_origins == "http://localhost:3000"
    assert server.template_directory == ".claude"


def test_server_config_validation_missing_name():
    """Test that ServerConfig requires name field."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        ServerConfig(directory="/tmp")


def test_server_config_validation_missing_directory():
    """Test that ServerConfig requires directory field."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        ServerConfig(name="test")


def test_server_config_rejects_extra_fields():
    """Test that ServerConfig rejects unknown fields."""
    with pytest.raises(Exception):  # Pydantic ValidationError due to extra="forbid"
        ServerConfig(
            name="test",
            directory="/tmp",
            unknown_field="value"
        )


def test_farm_config_minimal():
    """Test FarmConfig with minimal required fields."""
    farm = FarmConfig(
        servers=[
            ServerConfig(name="worker1", directory="/tmp")
        ]
    )

    assert farm.base_port == 3284  # default
    assert len(farm.servers) == 1
    assert farm.servers[0].name == "worker1"


def test_farm_config_multiple_servers():
    """Test FarmConfig with multiple servers."""
    farm = FarmConfig(
        base_port=4000,
        servers=[
            ServerConfig(name="worker1", agent_type="claude", directory="/tmp/w1"),
            ServerConfig(name="worker2", agent_type="cursor", directory="/tmp/w2", port=5000),
            ServerConfig(name="worker3", directory="/tmp/w3", skip_permissions=True)
        ]
    )

    assert farm.base_port == 4000
    assert len(farm.servers) == 3
    assert farm.servers[0].name == "worker1"
    assert farm.servers[0].agent_type == "claude"
    assert farm.servers[0].port is None  # will be auto-assigned to 4000
    assert farm.servers[1].name == "worker2"
    assert farm.servers[1].port == 5000  # explicitly set
    assert farm.servers[2].skip_permissions is True


def test_farm_config_rejects_extra_fields():
    """Test that FarmConfig rejects unknown fields."""
    with pytest.raises(Exception):  # Pydantic ValidationError due to extra="forbid"
        FarmConfig(
            servers=[ServerConfig(name="test", directory="/tmp")],
            unknown_field="value"
        )
