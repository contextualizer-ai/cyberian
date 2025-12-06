"""Tests for precondition checking."""

import os
import tempfile
from pathlib import Path

import pytest

from cyberian.models import (
    FilesExist,
    Preconditions,
    SyncTargets,
    Task,
)
from cyberian.runner import TaskRunner


def test_files_exist_model():
    """Test FilesExist model creation."""
    files_exist = FilesExist(patterns=["*.txt", "data.json"])
    assert files_exist.patterns == ["*.txt", "data.json"]
    assert files_exist.min_count is None


def test_files_exist_with_min_count():
    """Test FilesExist model with min_count."""
    files_exist = FilesExist(patterns=["*.csv"], min_count=5)
    assert files_exist.patterns == ["*.csv"]
    assert files_exist.min_count == 5


def test_preconditions_model():
    """Test Preconditions model creation."""
    preconditions = Preconditions(
        files_exist=FilesExist(patterns=["data/*.csv", "config.json"])
    )
    assert preconditions.files_exist is not None
    assert preconditions.files_exist.patterns == ["data/*.csv", "config.json"]


def test_task_with_preconditions():
    """Test Task model with preconditions."""
    task = Task(
        name="test-task",
        instructions="Do something",
        preconditions=Preconditions(
            files_exist=FilesExist(patterns=["input.txt"])
        )
    )
    assert task.preconditions is not None
    assert task.preconditions.files_exist.patterns == ["input.txt"]


def test_check_preconditions_success():
    """Test precondition check passes when files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "file1.txt").write_text("test1")
        (tmpdir_path / "file2.txt").write_text("test2")
        (tmpdir_path / "data.json").write_text("{}")

        # Create runner
        runner = TaskRunner(host="localhost", port=9999)

        # Create preconditions
        preconditions = Preconditions(
            files_exist=FilesExist(patterns=["*.txt", "data.json"])
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            # Should not raise
            runner._check_preconditions(preconditions)
        finally:
            os.chdir(original_dir)


def test_check_preconditions_fail_no_files():
    """Test precondition check fails when files don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create runner
        runner = TaskRunner(host="localhost", port=9999)

        # Create preconditions for non-existent files
        preconditions = Preconditions(
            files_exist=FilesExist(patterns=["nonexistent.txt"])
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            with pytest.raises(RuntimeError, match="Precondition failed: No files found matching"):
                runner._check_preconditions(preconditions)
        finally:
            os.chdir(original_dir)


def test_check_preconditions_glob_pattern():
    """Test precondition check with glob patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create subdirectory with files
        data_dir = tmpdir_path / "data"
        data_dir.mkdir()
        (data_dir / "file1.csv").write_text("data1")
        (data_dir / "file2.csv").write_text("data2")
        (data_dir / "file3.csv").write_text("data3")

        # Create runner
        runner = TaskRunner(host="localhost", port=9999)

        # Create preconditions
        preconditions = Preconditions(
            files_exist=FilesExist(patterns=["data/*.csv"])
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            # Should not raise (3 files match)
            runner._check_preconditions(preconditions)
        finally:
            os.chdir(original_dir)


def test_check_preconditions_min_count_success():
    """Test precondition check with min_count passes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create 5 files
        for i in range(5):
            (tmpdir_path / f"file{i}.txt").write_text(f"content{i}")

        # Create runner
        runner = TaskRunner(host="localhost", port=9999)

        # Create preconditions requiring at least 3 files
        preconditions = Preconditions(
            files_exist=FilesExist(patterns=["*.txt"], min_count=3)
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            # Should not raise (5 files >= 3 required)
            runner._check_preconditions(preconditions)
        finally:
            os.chdir(original_dir)


def test_check_preconditions_min_count_fail():
    """Test precondition check with min_count fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create only 2 files
        (tmpdir_path / "file1.txt").write_text("content1")
        (tmpdir_path / "file2.txt").write_text("content2")

        # Create runner
        runner = TaskRunner(host="localhost", port=9999)

        # Create preconditions requiring at least 5 files
        preconditions = Preconditions(
            files_exist=FilesExist(patterns=["*.txt"], min_count=5)
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            with pytest.raises(RuntimeError, match="matched 2 file\\(s\\), but minimum 5 required"):
                runner._check_preconditions(preconditions)
        finally:
            os.chdir(original_dir)


def test_check_preconditions_none():
    """Test that checking None preconditions is a no-op."""
    runner = TaskRunner(host="localhost", port=9999)
    # Should not raise
    runner._check_preconditions(None)


def test_preconditions_in_workflow():
    """Test loading workflow YAML with preconditions."""
    import yaml

    workflow_yaml = """
name: test-workflow
preconditions:
  files_exist:
    patterns:
      - data/*.csv
      - config.json
    min_count: 5

subtasks:
  process:
    instructions: Process the data
    preconditions:
      files_exist:
        patterns:
          - results/*.json
"""

    workflow_data = yaml.safe_load(workflow_yaml)
    task = Task(**workflow_data)

    # Check top-level preconditions
    assert task.preconditions is not None
    assert task.preconditions.files_exist is not None
    assert task.preconditions.files_exist.patterns == ["data/*.csv", "config.json"]
    assert task.preconditions.files_exist.min_count == 5

    # Check subtask preconditions
    process_task = task.subtasks["process"]
    assert process_task.preconditions is not None
    assert process_task.preconditions.files_exist is not None
    assert process_task.preconditions.files_exist.patterns == ["results/*.json"]


def test_preconditions_with_sync_targets():
    """Test Preconditions with sync_targets."""
    preconditions = Preconditions(
        files_exist=FilesExist(patterns=["abstracts/*.txt"]),
        sync_targets=SyncTargets(
            paths=["taxonomy.json", "scripts/"],
            description="Config and scripts"
        )
    )

    assert preconditions.files_exist is not None
    assert preconditions.sync_targets is not None
    assert preconditions.sync_targets.paths == ["taxonomy.json", "scripts/"]
    assert preconditions.sync_targets.description == "Config and scripts"


def test_preconditions_in_workflow_with_sync_targets():
    """Test loading workflow YAML with sync_targets in preconditions."""
    import yaml

    workflow_yaml = """
name: test-workflow
preconditions:
  files_exist:
    patterns:
      - abstracts/*.txt
      - taxonomy.json
  sync_targets:
    paths:
      - taxonomy.json
      - scripts/
    description: Required config and validation scripts

subtasks:
  tag:
    instructions: Tag the abstracts
"""

    workflow_data = yaml.safe_load(workflow_yaml)
    task = Task(**workflow_data)

    # Check preconditions with sync_targets
    assert task.preconditions is not None
    assert task.preconditions.files_exist is not None
    assert task.preconditions.files_exist.patterns == ["abstracts/*.txt", "taxonomy.json"]
    assert task.preconditions.sync_targets is not None
    assert task.preconditions.sync_targets.paths == ["taxonomy.json", "scripts/"]
    assert task.preconditions.sync_targets.description == "Required config and validation scripts"


def test_workflow_with_requirements():
    """Test loading workflow YAML with requirements."""
    import yaml

    workflow_yaml = """
name: test-workflow
requirements:
  agents:
    - name: claude-code
      level: RECOMMENDED
      reason: Best for file I/O
    - name: aider
      level: OPTIONAL
  dependencies:
    - name: python
      version: ">=3.10"
      level: REQUIRED
      reason: Uses match statement
  notes: This workflow reads multiple files

subtasks:
  task1:
    instructions: Do something
"""

    workflow_data = yaml.safe_load(workflow_yaml)
    task = Task(**workflow_data)

    # Check requirements
    assert task.requirements is not None
    assert len(task.requirements.agents) == 2
    assert task.requirements.agents[0].name == "claude-code"
    assert task.requirements.agents[0].level == "RECOMMENDED"
    assert task.requirements.agents[0].reason == "Best for file I/O"
    assert task.requirements.agents[1].name == "aider"
    assert task.requirements.agents[1].level == "OPTIONAL"

    assert len(task.requirements.dependencies) == 1
    assert task.requirements.dependencies[0].name == "python"
    assert task.requirements.dependencies[0].version == ">=3.10"
    assert task.requirements.dependencies[0].level == "REQUIRED"
    assert task.requirements.dependencies[0].reason == "Uses match statement"

    assert task.requirements.notes == "This workflow reads multiple files"
