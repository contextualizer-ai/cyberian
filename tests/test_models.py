"""Tests for models."""

import pytest

from cyberian.models import (
    AgentRequirement,
    DependencyRequirement,
    FarmConfig,
    ParamDefinition,
    Requirements,
    ServerConfig,
    SyncTargets,
    Task,
)


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


def test_sync_targets_minimal():
    """Test SyncTargets with minimal required fields."""
    sync = SyncTargets(paths=["taxonomy.json", "scripts/"])

    assert sync.paths == ["taxonomy.json", "scripts/"]
    assert sync.description is None


def test_sync_targets_with_description():
    """Test SyncTargets with description."""
    sync = SyncTargets(
        paths=["config.yaml", "lib/"],
        description="Configuration and library files"
    )

    assert sync.paths == ["config.yaml", "lib/"]
    assert sync.description == "Configuration and library files"


def test_agent_requirement_minimal():
    """Test AgentRequirement with minimal required fields."""
    agent = AgentRequirement(name="claude-code")

    assert agent.name == "claude-code"
    assert agent.level == "RECOMMENDED"  # default
    assert agent.reason is None
    assert agent.version is None


def test_agent_requirement_full():
    """Test AgentRequirement with all fields."""
    agent = AgentRequirement(
        name="aider",
        level="REQUIRED",
        reason="Needs git integration",
        version=">=0.40.0"
    )

    assert agent.name == "aider"
    assert agent.level == "REQUIRED"
    assert agent.reason == "Needs git integration"
    assert agent.version == ">=0.40.0"


def test_agent_requirement_levels():
    """Test AgentRequirement with different levels."""
    req = AgentRequirement(name="test", level="REQUIRED")
    assert req.level == "REQUIRED"

    rec = AgentRequirement(name="test", level="RECOMMENDED")
    assert rec.level == "RECOMMENDED"

    opt = AgentRequirement(name="test", level="OPTIONAL")
    assert opt.level == "OPTIONAL"


def test_agent_requirement_invalid_level():
    """Test that AgentRequirement rejects invalid levels."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        AgentRequirement(name="test", level="MAYBE")


def test_dependency_requirement_minimal():
    """Test DependencyRequirement with minimal required fields."""
    dep = DependencyRequirement(name="python")

    assert dep.name == "python"
    assert dep.version is None
    assert dep.level == "REQUIRED"  # default
    assert dep.reason is None


def test_dependency_requirement_full():
    """Test DependencyRequirement with all fields."""
    dep = DependencyRequirement(
        name="python",
        version=">=3.11",
        level="REQUIRED",
        reason="Uses match statement"
    )

    assert dep.name == "python"
    assert dep.version == ">=3.11"
    assert dep.level == "REQUIRED"
    assert dep.reason == "Uses match statement"


def test_dependency_requirement_levels():
    """Test DependencyRequirement with different levels."""
    req = DependencyRequirement(name="docker", level="REQUIRED")
    assert req.level == "REQUIRED"

    rec = DependencyRequirement(name="node", level="RECOMMENDED")
    assert rec.level == "RECOMMENDED"

    opt = DependencyRequirement(name="jq", level="OPTIONAL")
    assert opt.level == "OPTIONAL"


def test_requirements_empty():
    """Test Requirements with no requirements."""
    reqs = Requirements()

    assert reqs.agents == []
    assert reqs.dependencies == []
    assert reqs.notes is None


def test_requirements_with_agents():
    """Test Requirements with agent requirements."""
    reqs = Requirements(
        agents=[
            AgentRequirement(name="claude-code", level="RECOMMENDED"),
            AgentRequirement(name="aider", level="OPTIONAL")
        ]
    )

    assert len(reqs.agents) == 2
    assert reqs.agents[0].name == "claude-code"
    assert reqs.agents[0].level == "RECOMMENDED"
    assert reqs.agents[1].name == "aider"
    assert reqs.agents[1].level == "OPTIONAL"


def test_requirements_with_dependencies():
    """Test Requirements with dependency requirements."""
    reqs = Requirements(
        dependencies=[
            DependencyRequirement(name="python", version=">=3.10", level="REQUIRED"),
            DependencyRequirement(name="docker", level="OPTIONAL")
        ]
    )

    assert len(reqs.dependencies) == 2
    assert reqs.dependencies[0].name == "python"
    assert reqs.dependencies[0].version == ">=3.10"
    assert reqs.dependencies[1].name == "docker"


def test_requirements_full():
    """Test Requirements with all fields."""
    reqs = Requirements(
        agents=[AgentRequirement(name="claude-code")],
        dependencies=[DependencyRequirement(name="python", version=">=3.10")],
        notes="This workflow needs file I/O capabilities"
    )

    assert len(reqs.agents) == 1
    assert len(reqs.dependencies) == 1
    assert reqs.notes == "This workflow needs file I/O capabilities"


def test_task_with_requirements():
    """Test Task with requirements field."""
    task = Task(
        name="test-task",
        requirements=Requirements(
            agents=[AgentRequirement(name="claude-code", level="RECOMMENDED")],
            dependencies=[DependencyRequirement(name="python", version=">=3.11")]
        )
    )

    assert task.requirements is not None
    assert len(task.requirements.agents) == 1
    assert task.requirements.agents[0].name == "claude-code"
    assert len(task.requirements.dependencies) == 1
    assert task.requirements.dependencies[0].name == "python"
