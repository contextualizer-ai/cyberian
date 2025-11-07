"""Tests for farm command."""

from unittest.mock import MagicMock, patch

import yaml

from cyberian.cli import start_farm


def test_template_directory_copies_files(tmp_path):
    """Test that template_directory copies all files including hidden ones."""
    # Create template directory with files
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "config.txt").write_text("config content")
    (template_dir / ".hidden_file").write_text("hidden content")

    # Create hidden directory with file
    hidden_dir = template_dir / ".hidden_dir"
    hidden_dir.mkdir()
    (hidden_dir / "nested.txt").write_text("nested content")

    # Create working directory
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()

    # Create farm config
    farm_config = {
        "base_port": 4000,
        "servers": [
            {
                "name": "test-server",
                "agent_type": "claude",
                "directory": str(work_dir),
                "skip_permissions": True,
                "template_directory": "template"
            }
        ]
    }

    farm_file = tmp_path / "farm.yaml"
    farm_file.write_text(yaml.dump(farm_config))

    # Mock subprocess.Popen to avoid actually starting servers
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Run farm start
        start_farm(str(farm_file))

        # Check that subprocess was called (farm start completed)
        assert mock_popen.called

    # Verify files were copied
    assert (work_dir / "config.txt").exists()
    assert (work_dir / "config.txt").read_text() == "config content"
    assert (work_dir / ".hidden_file").exists()
    assert (work_dir / ".hidden_file").read_text() == "hidden content"
    assert (work_dir / ".hidden_dir").exists()
    assert (work_dir / ".hidden_dir" / "nested.txt").exists()
    assert (work_dir / ".hidden_dir" / "nested.txt").read_text() == "nested content"


def test_template_directory_overwrites_existing_files(tmp_path):
    """Test that template files overwrite existing files in working directory."""
    # Create template directory
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "config.txt").write_text("new content")

    # Create working directory with existing file
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()
    (work_dir / "config.txt").write_text("old content")

    # Create farm config
    farm_config = {
        "base_port": 4000,
        "servers": [
            {
                "name": "test-server",
                "agent_type": "claude",
                "directory": str(work_dir),
                "template_directory": "template"
            }
        ]
    }

    farm_file = tmp_path / "farm.yaml"
    farm_file.write_text(yaml.dump(farm_config))

    # Mock subprocess.Popen
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        start_farm(str(farm_file))

    # Verify file was overwritten
    assert (work_dir / "config.txt").read_text() == "new content"


def test_template_directory_missing_warns_but_continues(tmp_path, capsys):
    """Test that missing template directory warns but doesn't fail."""
    # Create working directory only (no template)
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()

    # Create farm config with non-existent template
    farm_config = {
        "base_port": 4000,
        "servers": [
            {
                "name": "test-server",
                "agent_type": "claude",
                "directory": str(work_dir),
                "template_directory": "nonexistent"
            }
        ]
    }

    farm_file = tmp_path / "farm.yaml"
    farm_file.write_text(yaml.dump(farm_config))

    # Mock subprocess.Popen
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        start_farm(str(farm_file))

        # Server should still start despite missing template
        assert mock_popen.called

    # Check warning was printed
    captured = capsys.readouterr()
    assert "Warning: Template directory" in captured.err
    assert "not found" in captured.err


def test_template_directory_not_a_directory_warns(tmp_path, capsys):
    """Test that template path that is a file (not directory) warns."""
    # Create template as a file instead of directory
    template_file = tmp_path / "template"
    template_file.write_text("not a directory")

    # Create working directory
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()

    # Create farm config
    farm_config = {
        "base_port": 4000,
        "servers": [
            {
                "name": "test-server",
                "agent_type": "claude",
                "directory": str(work_dir),
                "template_directory": "template"
            }
        ]
    }

    farm_file = tmp_path / "farm.yaml"
    farm_file.write_text(yaml.dump(farm_config))

    # Mock subprocess.Popen
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        start_farm(str(farm_file))

    # Check warning was printed
    captured = capsys.readouterr()
    assert "Warning: Template path" in captured.err
    assert "is not a directory" in captured.err


def test_no_template_directory_specified(tmp_path):
    """Test farm start works when no template_directory is specified."""
    # Create working directory
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()

    # Create farm config without template_directory
    farm_config = {
        "base_port": 4000,
        "servers": [
            {
                "name": "test-server",
                "agent_type": "claude",
                "directory": str(work_dir)
            }
        ]
    }

    farm_file = tmp_path / "farm.yaml"
    farm_file.write_text(yaml.dump(farm_config))

    # Mock subprocess.Popen
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        start_farm(str(farm_file))

        # Server should start normally
        assert mock_popen.called


def test_template_directory_copies_nested_structure(tmp_path):
    """Test that nested directory structures are copied correctly."""
    # Create complex template structure
    template_dir = tmp_path / "template"
    template_dir.mkdir()

    # Create nested directories
    (template_dir / "dir1").mkdir()
    (template_dir / "dir1" / "file1.txt").write_text("content1")
    (template_dir / "dir1" / "dir2").mkdir()
    (template_dir / "dir1" / "dir2" / "file2.txt").write_text("content2")

    # Create working directory
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()

    # Create farm config
    farm_config = {
        "base_port": 4000,
        "servers": [
            {
                "name": "test-server",
                "agent_type": "claude",
                "directory": str(work_dir),
                "template_directory": "template"
            }
        ]
    }

    farm_file = tmp_path / "farm.yaml"
    farm_file.write_text(yaml.dump(farm_config))

    # Mock subprocess.Popen
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        start_farm(str(farm_file))

    # Verify nested structure was copied
    assert (work_dir / "dir1").is_dir()
    assert (work_dir / "dir1" / "file1.txt").read_text() == "content1"
    assert (work_dir / "dir1" / "dir2").is_dir()
    assert (work_dir / "dir1" / "dir2" / "file2.txt").read_text() == "content2"
