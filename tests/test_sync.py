"""Tests for sync_targets functionality."""

from unittest.mock import Mock, patch

from typer.testing import CliRunner

from cyberian.cli import app

runner = CliRunner()


def test_sync_targets_copies_files(tmp_path):
    """Test that sync_targets copies files to working directory."""
    # Create workflow directory structure
    workflow_dir = tmp_path / "workflow"
    workflow_dir.mkdir()

    # Create files to sync
    (workflow_dir / "config.json").write_text('{"setting": "value"}')
    scripts_dir = workflow_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "validate.py").write_text("print('validation')")

    # Create workflow YAML with sync_targets
    workflow_file = workflow_dir / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
preconditions:
  sync_targets:
    paths:
      - config.json
      - scripts/
    description: Config and scripts
subtasks:
  task1:
    instructions: Do something
""")

    # Create separate working directory
    workdir = tmp_path / "workspace"
    workdir.mkdir()

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        runner.invoke(
            app,
            ["run", str(workflow_file), "--workdir", str(workdir)]
        )

        # Check files were synced
        assert (workdir / "config.json").exists()
        assert (workdir / "config.json").read_text() == '{"setting": "value"}'
        assert (workdir / "scripts").is_dir()
        assert (workdir / "scripts" / "validate.py").exists()


def test_sync_targets_creates_workdir(tmp_path):
    """Test that sync_targets creates working directory if it doesn't exist."""
    workflow_dir = tmp_path / "workflow"
    workflow_dir.mkdir()

    (workflow_dir / "data.txt").write_text("test data")

    workflow_file = workflow_dir / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
preconditions:
  sync_targets:
    paths:
      - data.txt
subtasks:
  task1:
    instructions: Do something
""")

    # Working directory doesn't exist yet
    workdir = tmp_path / "new-workspace"
    assert not workdir.exists()

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        runner.invoke(
            app,
            ["run", str(workflow_file), "--workdir", str(workdir)]
        )

        # Working directory should be created
        assert workdir.exists()
        assert (workdir / "data.txt").exists()


def test_sync_targets_updates_existing_files(tmp_path):
    """Test that sync_targets updates existing files in working directory."""
    workflow_dir = tmp_path / "workflow"
    workflow_dir.mkdir()

    # Create new version of file
    (workflow_dir / "config.json").write_text('{"version": 2}')

    workflow_file = workflow_dir / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
preconditions:
  sync_targets:
    paths:
      - config.json
subtasks:
  task1:
    instructions: Do something
""")

    workdir = tmp_path / "workspace"
    workdir.mkdir()

    # Create old version of file
    (workdir / "config.json").write_text('{"version": 1}')

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        runner.invoke(
            app,
            ["run", str(workflow_file), "--workdir", str(workdir)]
        )

        # File should be updated
        assert (workdir / "config.json").read_text() == '{"version": 2}'


def test_sync_targets_skips_missing_files(tmp_path):
    """Test that sync_targets skips missing files with warning."""
    workflow_dir = tmp_path / "workflow"
    workflow_dir.mkdir()

    workflow_file = workflow_dir / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
preconditions:
  sync_targets:
    paths:
      - missing.txt
      - nonexistent/
subtasks:
  task1:
    instructions: Do something
""")

    workdir = tmp_path / "workspace"
    workdir.mkdir()

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        result = runner.invoke(
            app,
            ["run", str(workflow_file), "--workdir", str(workdir), "-v"]
        )

        # Should complete without error (files skipped)
        assert result.exit_code == 0
        assert not (workdir / "missing.txt").exists()
        assert not (workdir / "nonexistent").exists()


def test_no_sync_when_no_sync_targets(tmp_path):
    """Test that no sync happens when sync_targets not specified."""
    workflow_dir = tmp_path / "workflow"
    workflow_dir.mkdir()

    (workflow_dir / "config.json").write_text('{"test": true}')

    workflow_file = workflow_dir / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
subtasks:
  task1:
    instructions: Do something
""")

    workdir = tmp_path / "workspace"
    workdir.mkdir()

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        runner.invoke(
            app,
            ["run", str(workflow_file), "--workdir", str(workdir)]
        )

        # File should NOT be synced
        assert not (workdir / "config.json").exists()


def test_sync_targets_with_trailing_slash(tmp_path):
    """Test that paths with trailing slash are treated as directories."""
    workflow_dir = tmp_path / "workflow"
    workflow_dir.mkdir()

    # Create directory
    lib_dir = workflow_dir / "lib"
    lib_dir.mkdir()
    (lib_dir / "utils.py").write_text("def helper(): pass")

    workflow_file = workflow_dir / "workflow.yaml"
    workflow_file.write_text("""
name: test-workflow
preconditions:
  sync_targets:
    paths:
      - lib/
subtasks:
  task1:
    instructions: Do something
""")

    workdir = tmp_path / "workspace"
    workdir.mkdir()

    with patch("cyberian.runner.TaskRunner") as mock_runner_class:
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        runner.invoke(
            app,
            ["run", str(workflow_file), "--workdir", str(workdir)]
        )

        # Directory should be synced (without double slash)
        assert (workdir / "lib").is_dir()
        assert (workdir / "lib" / "utils.py").exists()
