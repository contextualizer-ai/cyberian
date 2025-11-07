"""Tests for the run command."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from cyberian.cli import app

runner = CliRunner()


def test_run_command_with_dir_option(tmp_path):
    """Test run command changes directory when --dir option is provided."""
    # Create a temporary workflow file
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Do something
""")

    with patch("cyberian.cli.os.chdir") as mock_chdir, \
         patch("cyberian.runner.TaskRunner") as mock_runner_class:

        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--dir", "/tmp/test-dir"]
        )

        assert result.exit_code == 0
        mock_chdir.assert_called_once_with("/tmp/test-dir")
        mock_runner.run_task.assert_called_once()


def test_run_command_without_dir_option(tmp_path):
    """Test run command does not change directory when --dir option is not provided."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Do something
""")

    with patch("cyberian.cli.os.chdir") as mock_chdir, \
         patch("cyberian.runner.TaskRunner") as mock_runner_class:

        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(app, ["run", str(workflow_file)])

        assert result.exit_code == 0
        mock_chdir.assert_not_called()
        mock_runner.run_task.assert_called_once()


def test_run_command_with_agent_type(tmp_path):
    """Test run command accepts --agent-type option."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Do something with {{agent_type}}
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--agent-type", "claude"]
        )

        assert result.exit_code == 0
        # Check that context was passed with agent_type
        call_args = mock_runner.run_task.call_args
        context = call_args[0][1]
        assert context.get("agent_type") == "claude"


def test_run_command_agent_type_in_context(tmp_path):
    """Test that agent_type is available in template context."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Use {{agent_type}} to analyze
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--agent-type", "aider"]
        )

        assert result.exit_code == 0
        context = mock_runner.run_task.call_args[0][1]
        assert "agent_type" in context
        assert context["agent_type"] == "aider"


def test_run_command_with_dir_and_agent_type(tmp_path):
    """Test run command with both --dir and --agent-type options."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Run {{agent_type}} analysis
""")

    with patch("cyberian.cli.os.chdir") as mock_chdir, \
         patch("cyberian.runner.TaskRunner") as mock_runner_class:

        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            [
                "run", str(workflow_file),
                "--dir", "/my/project",
                "--agent-type", "cursor"
            ]
        )

        assert result.exit_code == 0
        mock_chdir.assert_called_once_with("/my/project")
        context = mock_runner.run_task.call_args[0][1]
        assert context["agent_type"] == "cursor"


def test_run_command_with_params_and_agent_type(tmp_path):
    """Test that --param and --agent-type work together."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
params:
  query:
    range: string
    required: true
instructions: Use {{agent_type}} to research {{query}}
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            [
                "run", str(workflow_file),
                "--param", "query=AI",
                "--agent-type", "claude"
            ]
        )

        assert result.exit_code == 0
        context = mock_runner.run_task.call_args[0][1]
        assert context["query"] == "AI"
        assert context["agent_type"] == "claude"


def test_run_command_param_overrides_agent_type():
    """Test that explicit --param agent_type overrides --agent-type option."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
name: test
instructions: Use {{agent_type}}
""")
        workflow_file = f.name

    try:
        with patch("cyberian.runner.TaskRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner

            result = runner.invoke(
                app,
                [
                    "run", workflow_file,
                    "--agent-type", "claude",
                    "--param", "agent_type=custom-override"
                ]
            )

            assert result.exit_code == 0
            context = mock_runner.run_task.call_args[0][1]
            # Explicit param should override the flag
            assert context["agent_type"] == "custom-override"
    finally:
        Path(workflow_file).unlink()


@pytest.mark.parametrize(
    "dir_path,agent_type",
    [
        ("/tmp/project1", "claude"),
        ("/home/user/code", "aider"),
        ("./relative/path", "cursor"),
    ]
)
def test_run_command_parametrized(tmp_path, dir_path, agent_type):
    """Parametrized test for different --dir and --agent-type combinations."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test
instructions: Test
""")

    with patch("cyberian.cli.os.chdir") as mock_chdir, \
         patch("cyberian.runner.TaskRunner") as mock_runner_class:

        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--dir", dir_path, "--agent-type", agent_type]
        )

        assert result.exit_code == 0
        mock_chdir.assert_called_once_with(dir_path)
        context = mock_runner.run_task.call_args[0][1]
        assert context["agent_type"] == agent_type


def test_run_command_with_skip_permissions(tmp_path):
    """Test run command accepts --skip-permissions option."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Do something
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--skip-permissions"]
        )

        assert result.exit_code == 0
        # Check that context was passed with skip_permissions
        call_args = mock_runner.run_task.call_args
        context = call_args[0][1]
        assert context.get("skip_permissions") is True


def test_run_command_skip_permissions_in_context(tmp_path):
    """Test that skip_permissions is available in template context."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Run with skip={{skip_permissions}}
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--skip-permissions"]
        )

        assert result.exit_code == 0
        context = mock_runner.run_task.call_args[0][1]
        assert "skip_permissions" in context
        assert context["skip_permissions"] is True


def test_run_command_with_agent_type_and_skip_permissions(tmp_path):
    """Test run command with both --agent-type and --skip-permissions options."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Run {{agent_type}} analysis
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            [
                "run", str(workflow_file),
                "--agent-type", "claude",
                "--skip-permissions"
            ]
        )

        assert result.exit_code == 0
        context = mock_runner.run_task.call_args[0][1]
        assert context["agent_type"] == "claude"
        assert context["skip_permissions"] is True


def test_run_command_with_resume_from(tmp_path):
    """Test run command with --resume-from option."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Test workflow
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--resume-from", "iterate"]
        )

        assert result.exit_code == 0
        # Check that TaskRunner was initialized with resume_from
        init_kwargs = mock_runner_class.call_args[1]
        assert init_kwargs["resume_from"] == "iterate"


def test_run_command_resume_from_in_output(tmp_path):
    """Test that resume-from message appears in output."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
instructions: Test
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--resume-from", "task2"]
        )

        assert result.exit_code == 0
        assert "Resuming workflow from: task2" in result.output


def test_run_command_param_type_integer(tmp_path):
    """Test that integer params are parsed as integers, not strings."""
    from unittest.mock import patch

    # Create a workflow file
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
params:
  count:
    range: integer
    required: true
subtasks:
  task1:
    instructions: "Do something {{count}} times"
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = mock_runner_class.return_value

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "-p", "count=42"]
        )

        assert result.exit_code == 0

        # Check that run_task was called with integer, not string
        run_task_call = mock_runner.run_task.call_args
        context = run_task_call[0][1]

        assert "count" in context
        assert context["count"] == 42  # Should be int
        assert isinstance(context["count"], int)


def test_run_command_param_type_boolean(tmp_path):
    """Test that boolean params are parsed as booleans."""
    from unittest.mock import patch

    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
params:
  enabled:
    range: boolean
    required: true
subtasks:
  task1:
    instructions: "Check if enabled: {{enabled}}"
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = mock_runner_class.return_value

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "-p", "enabled=true"]
        )

        assert result.exit_code == 0

        run_task_call = mock_runner.run_task.call_args
        context = run_task_call[0][1]

        assert context["enabled"] is True  # Should be bool, not string "true"
        assert isinstance(context["enabled"], bool)


def test_run_command_param_type_string_with_quotes(tmp_path):
    """Test that quoted strings are parsed correctly."""
    from unittest.mock import patch

    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
params:
  message:
    range: string
    required: true
subtasks:
  task1:
    instructions: "Say: {{message}}"
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = mock_runner_class.return_value

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "-p", 'message="hello world"']
        )

        assert result.exit_code == 0

        run_task_call = mock_runner.run_task.call_args
        context = run_task_call[0][1]

        assert context["message"] == "hello world"
        assert isinstance(context["message"], str)


def test_run_command_param_type_url(tmp_path):
    """Test that URLs are kept as strings."""
    from unittest.mock import patch

    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
params:
  url:
    range: string
    required: true
subtasks:
  task1:
    instructions: "Fetch: {{url}}"
""")

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = mock_runner_class.return_value

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "-p", "url=https://example.com/doc.pdf"]
        )

        assert result.exit_code == 0

        run_task_call = mock_runner.run_task.call_args
        context = run_task_call[0][1]

        assert context["url"] == "https://example.com/doc.pdf"
        assert isinstance(context["url"], str)
