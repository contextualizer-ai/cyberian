"""Pydantic models for cyberian task/workflow definitions."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ServerConfig(BaseModel):
    """Configuration for a single server in a farm."""

    name: str = Field(..., description="Logical name for this server")
    agent_type: str = Field(default="custom", description="Agent type (e.g., aider, claude, cursor, goose)")
    port: Optional[int] = Field(default=None, description="Port to run the server on (auto-assigned if not specified)")
    directory: str = Field(..., description="Working directory for the server")
    skip_permissions: bool = Field(default=False, description="Skip permission checks")
    allowed_hosts: Optional[str] = Field(default=None, description="HTTP allowed hosts (comma-separated)")
    allowed_origins: Optional[str] = Field(default=None, description="HTTP allowed origins (comma-separated)")
    template_directory: Optional[str] = Field(
        default=None,
        description="Template directory (relative to farm config file) to copy to working directory"
    )

    model_config = ConfigDict(extra="forbid")


class FarmConfig(BaseModel):
    """Configuration for a farm of servers."""

    base_port: int = Field(default=3284, description="Base port for auto-assignment (first server gets this port)")
    servers: list[ServerConfig] = Field(..., description="List of server configurations")

    model_config = ConfigDict(extra="forbid")


class ParamDefinition(BaseModel):
    """Definition of a task parameter."""

    range: str = Field(..., description="Parameter type/range (e.g., 'string', 'integer')")
    required: bool = Field(default=False, description="Whether this parameter is required")
    examples: list[Any] = Field(default_factory=list, description="Example values for this parameter")


class LoopCondition(BaseModel):
    """Condition for looping a task."""

    status: str = Field(..., description="Status value to match for loop termination")
    message: str = Field(..., description="Message/instructions for the agent about the loop condition")


class SuccessCriteria(BaseModel):
    """Success criteria for validating task completion."""

    python: str = Field(..., description="Python code to execute for validation. Must set result = True/False.")
    max_retries: int = Field(default=0, description="Maximum number of retry attempts if validation fails (0 = fail fast)")
    retry_message: Optional[str] = Field(
        default=None,
        description="Message to send to agent on validation failure. Supports Jinja2 template with {{error}} variable."
    )


class ProviderCall(BaseModel):
    """Configuration for calling an external provider instead of using an agent.

    When a task has a provider_call, the task runner will execute the provider
    directly rather than sending instructions to an agent. This is useful for
    deterministic operations like research, data retrieval, or API calls.

    Example:
        >>> call = ProviderCall(
        ...     provider="deep-research-client",
        ...     method="research",
        ...     params={"query": "CRISPR", "providers": ["openai"]},
        ...     output_file="results.md"
        ... )
    """

    provider: str = Field(..., description="Provider name (e.g., 'deep-research-client', 'semantic-scholar')")
    method: str = Field(..., description="Method to call on the provider (e.g., 'research', 'search')")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the provider method (supports Jinja2 templates)")
    output_file: Optional[str] = Field(default=None, description="Optional file path to save results (supports Jinja2 templates)")

    model_config = ConfigDict(extra="forbid")


class Task(BaseModel):
    """Recursive task definition (Russian doll model).

    A task can be a top-level workflow or a nested subtask.
    Each task can contain its own subtasks, allowing for arbitrary nesting.
    """

    name: Optional[str] = Field(default=None, description="Name of the task (required for top-level)")
    description: Optional[str] = Field(default=None, description="Description of what this task does")
    requires_workdir: bool = Field(
        default=False, description="Whether this task requires a working directory"
    )
    params: dict[str, ParamDefinition] = Field(
        default_factory=dict, description="Parameters for this task"
    )
    instructions: Optional[str] = Field(
        default=None, description="Instructions for executing this task"
    )
    system_instructions: Optional[str] = Field(
        default=None, description="System-level instructions inherited by all subtasks (Jinja2 template)"
    )
    provider_call: Optional[ProviderCall] = Field(
        default=None, description="Optional provider call (mutually exclusive with instructions - provider calls don't use agents)"
    )
    subtasks: dict[str, Task] = Field(
        default_factory=dict, description="Subtasks that make up this task (recursive)"
    )
    loop_until: Optional[LoopCondition] = Field(
        default=None, description="Optional loop condition for this task"
    )
    success_criteria: Optional[SuccessCriteria] = Field(
        default=None, description="Optional success criteria to validate task completion"
    )
    agent_lifecycle: Optional[str] = Field(
        default=None,
        description="Agent server lifecycle mode: 'reuse' (default, keeps server) or 'refresh' (restarts between tasks)"
    )

    model_config = ConfigDict(extra="forbid")
