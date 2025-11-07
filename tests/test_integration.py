"""Integration tests that run against a real agentapi server.

These tests are skipped by default. To run them:
1. Start an agentapi server: uv run cyberian server claude --skip-permissions
2. Run: uv run pytest tests/test_integration.py -v
   or: uv run pytest -v -m integration

To skip these tests (default): uv run pytest -v -m "not integration"
"""


import httpx
import pytest

from cyberian.models import Task
from cyberian.runner import TaskRunner


def is_server_running(host="localhost", port=3284):
    """Check if an agentapi server is running."""
    try:
        response = httpx.get(f"http://{host}:{port}/status", timeout=1.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


@pytest.mark.integration
@pytest.mark.skipif(
    not is_server_running(),
    reason="No agentapi server running on localhost:3284. Start with: cyberian server claude --skip-permissions"
)
class TestIntegration:
    """Integration tests that require a running agentapi server."""

    def test_simple_math_workflow(self):
        """Test the simple-math workflow with 3 sequential steps."""
        import yaml

        # Load the workflow
        with open("tests/examples/simple-math.yaml") as f:
            workflow_data = yaml.safe_load(f)

        task = Task(**workflow_data)
        context = {"input_number": 10}

        # Run the workflow
        runner = TaskRunner(timeout=60, poll_interval=1.0)
        runner.run_task(task, context)

        # Verify we can query messages and see the results
        response = httpx.get("http://localhost:3284/messages")
        assert response.status_code == 200

        messages = response.json().get("messages", [])
        agent_messages = [m for m in messages if m.get("role") == "agent"]

        # Should have at least 3 agent responses (one per step)
        assert len(agent_messages) >= 3, f"Expected at least 3 agent messages, got {len(agent_messages)}"

        # Verify completion statuses in messages
        all_content = " ".join([m.get("content", "") for m in agent_messages])
        completion_count = all_content.count("COMPLETION_STATUS: COMPLETE")
        assert completion_count >= 3, f"Expected 3 COMPLETE statuses, found {completion_count}"

    def test_simple_math_workflow_with_resume(self):
        """Test resuming the simple-math workflow from step2."""
        import yaml

        # Load the workflow
        with open("tests/examples/simple-math.yaml") as f:
            workflow_data = yaml.safe_load(f)

        task = Task(**workflow_data)
        context = {"input_number": 5}

        # Run the workflow resuming from step2 (should skip step1)
        runner = TaskRunner(timeout=60, poll_interval=1.0, resume_from="step2")
        runner.run_task(task, context)

        # Verify we can query messages
        response = httpx.get("http://localhost:3284/messages")
        assert response.status_code == 200

        messages = response.json().get("messages", [])
        agent_messages = [m for m in messages if m.get("role") == "agent"]

        # Should have at least 2 agent responses (step2 and step3)
        assert len(agent_messages) >= 2, f"Expected at least 2 agent messages, got {len(agent_messages)}"

    @pytest.mark.parametrize("input_num,expected_sum", [
        (0, 6),   # 0 + 1 + 2 + 3 = 6
        (10, 16), # 10 + 1 + 2 + 3 = 16
        (100, 106), # 100 + 1 + 2 + 3 = 106
    ])
    def test_simple_math_with_different_inputs(self, input_num, expected_sum):
        """Test simple-math workflow with different input numbers."""
        import yaml

        with open("tests/examples/simple-math.yaml") as f:
            workflow_data = yaml.safe_load(f)

        task = Task(**workflow_data)
        context = {"input_number": input_num}

        runner = TaskRunner(timeout=60, poll_interval=1.0)
        runner.run_task(task, context)

        # Get the last agent message
        response = httpx.get("http://localhost:3284/messages")
        messages = response.json().get("messages", [])
        agent_messages = [m for m in messages if m.get("role") == "agent"]

        assert len(agent_messages) >= 3

        # Check for the final result in messages
        all_content = " ".join([m.get("content", "") for m in agent_messages])

        # Look for the expected sum somewhere in the messages
        # The agent should mention the final result
        assert str(expected_sum) in all_content, f"Expected to find {expected_sum} in agent messages"
