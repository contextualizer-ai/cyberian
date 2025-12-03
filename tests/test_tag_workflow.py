"""Test the document tagging workflow with external success criteria script."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from cyberian.models import Task
from cyberian.runner import TaskRunner


def test_success_criteria_with_external_script():
    """Test that external success criteria scripts work correctly."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a simple test script
        script_path = tmpdir_path / "check.py"
        script_path.write_text("""
import os
# Check that output.txt exists
result = os.path.exists("output.txt")
""")

        # Create workflow YAML path (for script resolution)
        workflow_path = tmpdir_path / "workflow.yaml"

        # Create task with external script
        task = Task(
            name="test-task",
            instructions="Create a file called output.txt",
            success_criteria={
                "script": "check.py",
                "max_retries": 1
            }
        )

        # Initialize runner
        runner = TaskRunner(
            host="localhost",
            port=9999,  # Won't actually connect in this unit test
            workflow_file=str(workflow_path)
        )

        # Change to tmpdir for execution
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Test that script fails when file doesn't exist
            success, error = runner._check_success_criteria(task.success_criteria, {})
            assert not success, "Should fail when output.txt doesn't exist"

            # Create the file
            (tmpdir_path / "output.txt").write_text("test")

            # Test that script passes now
            success, error = runner._check_success_criteria(task.success_criteria, {})
            assert success, f"Should pass when output.txt exists: {error}"
            assert error is None

        finally:
            os.chdir(original_dir)


def test_tag_workflow_structure():
    """Test that the tag-documents workflow is properly structured."""
    workflow_path = Path(__file__).parent / "examples" / "tag-documents" / "tag-workflow.yaml"

    assert workflow_path.exists(), "tag-workflow.yaml should exist"

    # Load and validate the workflow
    import yaml
    with open(workflow_path) as f:
        workflow_data = yaml.safe_load(f)

    # Validate structure
    assert "name" in workflow_data
    assert workflow_data["name"] == "tag-documents"
    assert "subtasks" in workflow_data
    assert "tag_abstracts" in workflow_data["subtasks"]

    # Check success criteria uses external script
    task_data = workflow_data["subtasks"]["tag_abstracts"]
    assert "success_criteria" in task_data
    assert "script" in task_data["success_criteria"]
    assert task_data["success_criteria"]["script"] == "scripts/validate_tags.py"
    assert task_data["success_criteria"]["max_retries"] == 3


def test_validate_tags_script_exists():
    """Test that the validation script exists and is executable."""
    script_path = (
        Path(__file__).parent / "examples" / "tag-documents" / "scripts" / "validate_tags.py"
    )

    assert script_path.exists(), "validate_tags.py should exist"

    # Check script has proper structure
    content = script_path.read_text()
    assert "result =" in content, "Script must set 'result' variable"
    assert "import json" in content, "Script should import json"


def test_abstracts_and_taxonomy_exist():
    """Test that all test data files exist."""
    base_path = Path(__file__).parent / "examples" / "tag-documents"

    # Check taxonomy
    taxonomy_path = base_path / "taxonomy.json"
    assert taxonomy_path.exists(), "taxonomy.json should exist"

    with open(taxonomy_path) as f:
        taxonomy = json.load(f)

    assert "allowed_tags" in taxonomy
    assert isinstance(taxonomy["allowed_tags"], list)
    assert len(taxonomy["allowed_tags"]) > 0

    # Check abstracts directory
    abstracts_dir = base_path / "abstracts"
    assert abstracts_dir.exists(), "abstracts directory should exist"

    # Check we have 20 abstracts
    abstract_files = list(abstracts_dir.glob("abstract_*.txt"))
    assert len(abstract_files) == 20, f"Should have 20 abstracts, found {len(abstract_files)}"

    # Check they're numbered correctly
    for i in range(1, 21):
        abstract_path = abstracts_dir / f"abstract_{i:03d}.txt"
        assert abstract_path.exists(), f"abstract_{i:03d}.txt should exist"
        assert abstract_path.stat().st_size > 0, f"abstract_{i:03d}.txt should not be empty"


def test_validation_script_catches_errors():
    """Test that the validation script properly catches various error conditions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test data
        abstracts_dir = tmpdir_path / "abstracts"
        abstracts_dir.mkdir()

        # Create a few test abstracts
        (abstracts_dir / "abstract_001.txt").write_text("Test abstract 1")
        (abstracts_dir / "abstract_002.txt").write_text("Test abstract 2")

        # Create taxonomy
        taxonomy = {"allowed_tags": ["tag1", "tag2", "tag3"]}
        (tmpdir_path / "taxonomy.json").write_text(json.dumps(taxonomy))

        # Copy validation script
        script_source = (
            Path(__file__).parent / "examples" / "tag-documents" / "scripts" / "validate_tags.py"
        )
        script_dest = tmpdir_path / "validate_tags.py"
        script_dest.write_text(script_source.read_text())

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Helper to create namespace with necessary builtins for the validation script
            def create_namespace():
                return {
                    "__builtins__": {
                        "__import__": __import__,
                        "len": len,
                        "open": open,
                        "str": str,
                        "set": set,
                        "sorted": sorted,
                        "Exception": Exception,
                        "ValueError": ValueError,
                        "FileNotFoundError": FileNotFoundError,
                    }
                }

            # Test 1: Missing tags.json
            namespace = create_namespace()
            exec(script_dest.read_text(), namespace)
            assert namespace["result"] is False, "Should fail when tags.json missing"

            # Test 2: Invalid JSON
            (tmpdir_path / "tags.json").write_text("not valid json")
            namespace = create_namespace()
            exec(script_dest.read_text(), namespace)
            assert namespace["result"] is False, "Should fail with invalid JSON"

            # Test 3: Wrong structure
            (tmpdir_path / "tags.json").write_text('{"wrong": "structure"}')
            namespace = create_namespace()
            exec(script_dest.read_text(), namespace)
            assert namespace["result"] is False, "Should fail with wrong structure"

            # Test 4: Invalid tags
            tags_data = {
                "documents": [
                    {"filename": "abstract_001.txt", "tags": ["invalid_tag", "tag1"]},
                    {"filename": "abstract_002.txt", "tags": ["tag2", "tag3"]}
                ]
            }
            (tmpdir_path / "tags.json").write_text(json.dumps(tags_data))
            namespace = create_namespace()
            exec(script_dest.read_text(), namespace)
            assert namespace["result"] is False, "Should fail with invalid tags"

            # Test 5: Too few tags
            tags_data = {
                "documents": [
                    {"filename": "abstract_001.txt", "tags": ["tag1"]},  # Only 1 tag
                    {"filename": "abstract_002.txt", "tags": ["tag2", "tag3"]}
                ]
            }
            (tmpdir_path / "tags.json").write_text(json.dumps(tags_data))
            namespace = create_namespace()
            exec(script_dest.read_text(), namespace)
            assert namespace["result"] is False, "Should fail with too few tags"

            # Test 6: Valid tags
            tags_data = {
                "documents": [
                    {"filename": "abstract_001.txt", "tags": ["tag1", "tag2"]},
                    {"filename": "abstract_002.txt", "tags": ["tag2", "tag3"]}
                ]
            }
            (tmpdir_path / "tags.json").write_text(json.dumps(tags_data))
            namespace = create_namespace()
            exec(script_dest.read_text(), namespace)
            assert namespace["result"] is True, "Should pass with valid tags"

        finally:
            os.chdir(original_dir)


def is_server_running(host="localhost", port=3284):
    """Check if an agentapi server is running."""
    import httpx
    try:
        response = httpx.get(f"http://{host}:{port}/status", timeout=1.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.skipif(
    not is_server_running(),
    reason="No agentapi server running. Start with: uv run cyberian server claude --skip-permissions"
)
def test_tag_workflow_integration():
    """Integration test for the full tagging workflow with a real LLM agent.

    NOTE: This test requires:
    1. A running agentapi server (start with: uv run cyberian server claude --skip-permissions)
    2. An LLM agent that can read files and create JSON output
    3. May be slow and expensive (uses real LLM calls)

    This test is skipped by default (see pytest.ini addopts).
    Run with: pytest -m integration -m llm
    """
    import shutil
    import yaml

    workflow_path = Path(__file__).parent / "examples" / "tag-documents" / "tag-workflow.yaml"
    example_dir = workflow_path.parent

    with open(workflow_path) as f:
        workflow_data = yaml.safe_load(f)

    task = Task(**workflow_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Copy all test data to temp directory
        shutil.copytree(example_dir / "abstracts", tmpdir_path / "abstracts")
        shutil.copy(example_dir / "taxonomy.json", tmpdir_path / "taxonomy.json")
        shutil.copytree(example_dir / "scripts", tmpdir_path / "scripts")

        # Run the workflow
        runner = TaskRunner(
            host="localhost",
            port=3284,
            timeout=300,
            workflow_file=str(workflow_path)
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            runner.run_task(task, {})

            # Verify tags.json was created and is valid
            assert (tmpdir_path / "tags.json").exists()

            with open(tmpdir_path / "tags.json") as f:
                tags = json.load(f)

            assert "documents" in tags
            assert len(tags["documents"]) == 20

            # Verify all tags are from taxonomy
            with open(tmpdir_path / "taxonomy.json") as f:
                taxonomy = json.load(f)

            allowed_tags = set(taxonomy["allowed_tags"])
            for doc in tags["documents"]:
                assert 2 <= len(doc["tags"]) <= 4
                assert set(doc["tags"]).issubset(allowed_tags)

        finally:
            os.chdir(original_dir)
