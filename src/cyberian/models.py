"""Pydantic models for cyberian task/workflow definitions."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServerConfig(BaseModel):
    """Configuration for a single server in a farm."""

    name: str = Field(..., description="Logical name for this server")
    agent_type: str = Field(default="custom", description="Agent type (e.g., aider, claude, codex, cursor, goose)")
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
    """Success criteria for validating task completion.

    Either 'python' (inline code) or 'script' (external file) must be provided, but not both.
    The script/code must set a variable named 'result' to True (success) or False (failure).

    If the script exits with non-zero status or raises an exception, the error message
    will be fed back to the agent in the retry_message.
    """

    python: Optional[str] = Field(
        default=None,
        description="Inline Python code to execute for validation. Must set result = True/False."
    )
    script: Optional[str] = Field(
        default=None,
        description="Path to external Python script for validation (relative to workflow file). Must set result = True/False."
    )
    max_retries: int = Field(default=0, description="Maximum number of retry attempts if validation fails (0 = fail fast)")
    retry_message: Optional[str] = Field(
        default=None,
        description="Message to send to agent on validation failure. Supports Jinja2 template with {{error}} variable."
    )

    @model_validator(mode='after')
    def check_python_or_script(self) -> 'SuccessCriteria':
        """Validate that exactly one of python or script is provided."""
        if self.python is not None and self.script is not None:
            raise ValueError("Cannot specify both 'python' and 'script' - choose one")
        if self.python is None and self.script is None:
            raise ValueError("Must specify either 'python' or 'script'")
        return self


class FilesExist(BaseModel):
    """Check that files exist before task execution.

    Supports glob patterns. Future: could add min_count for globs.

    Example:
        >>> check = FilesExist(patterns=["abstracts/*.txt", "taxonomy.json"])
    """

    patterns: list[str] = Field(
        ...,
        description="List of file paths or glob patterns to check. All must exist."
    )
    min_count: Optional[int] = Field(
        default=None,
        description="Minimum number of files that must match (for glob patterns). If None, at least 1 required."
    )


class SyncTargets(BaseModel):
    """Files/directories that should be synced to workspace before execution.

    These are typically configuration files, scripts, or data files needed by the workflow.
    Unlike files_exist (which just checks), sync_targets indicates what should be copied
    when using --workdir with a separate workspace.

    Example:
        >>> sync = SyncTargets(
        ...     paths=["taxonomy.json", "scripts/"],
        ...     description="Taxonomy and validation scripts needed for workflow"
        ... )
    """

    paths: list[str] = Field(
        ...,
        description="List of file paths or directories to sync. Paths ending with / are treated as directories."
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of what these files are for"
    )


class Preconditions(BaseModel):
    """Preconditions that must be met before task execution.

    Checked before starting task. Fails fast with clear error messages.

    Example:
        >>> preconditions = Preconditions(
        ...     files_exist=FilesExist(patterns=["data/*.csv", "config.json"]),
        ...     sync_targets=SyncTargets(paths=["config.json", "scripts/"])
        ... )
    """

    files_exist: Optional[FilesExist] = Field(
        default=None,
        description="Files that must exist before task execution"
    )
    sync_targets: Optional[SyncTargets] = Field(
        default=None,
        description="Files/directories to sync when using workspace mode (informational for now)"
    )


class AgentRequirement(BaseModel):
    """Specification for required/recommended agent.

    Example:
        >>> req = AgentRequirement(
        ...     name="claude-code",
        ...     level="RECOMMENDED",
        ...     reason="Works best with file manipulation capabilities"
        ... )
    """

    name: str = Field(..., description="Agent name (e.g., 'claude-code', 'aider', 'cursor')")
    level: Literal["REQUIRED", "RECOMMENDED", "OPTIONAL"] = Field(
        default="RECOMMENDED",
        description="Requirement level"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Why this agent is required/recommended"
    )
    version: Optional[str] = Field(
        default=None,
        description="Minimum version if applicable"
    )


class DependencyRequirement(BaseModel):
    """External dependency requirement.

    Example:
        >>> dep = DependencyRequirement(
        ...     name="python",
        ...     version=">=3.11",
        ...     level="REQUIRED",
        ...     reason="Scripts use match statement"
        ... )
    """

    name: str = Field(..., description="Dependency name (e.g., 'python', 'node', 'docker')")
    version: Optional[str] = Field(
        default=None,
        description="Version constraint (e.g., '>=3.11', '~=1.0')"
    )
    level: Literal["REQUIRED", "RECOMMENDED", "OPTIONAL"] = Field(
        default="REQUIRED",
        description="Requirement level"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Why this dependency is needed"
    )


class Requirements(BaseModel):
    """Workflow requirements (agents, dependencies, etc.).

    Informational/documentation only for now. Future: could validate before execution.

    Example:
        >>> reqs = Requirements(
        ...     agents=[AgentRequirement(name="claude-code", level="RECOMMENDED")],
        ...     dependencies=[DependencyRequirement(name="python", version=">=3.11")]
        ... )
    """

    agents: list[AgentRequirement] = Field(
        default_factory=list,
        description="Agent requirements (which agents work best)"
    )
    dependencies: list[DependencyRequirement] = Field(
        default_factory=list,
        description="External dependencies (python, node, etc.)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes about requirements"
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
    requirements: Optional[Requirements] = Field(
        default=None, description="Workflow requirements (agents, dependencies, etc.) - informational only"
    )
    preconditions: Optional[Preconditions] = Field(
        default=None, description="Preconditions that must be met before task execution"
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
