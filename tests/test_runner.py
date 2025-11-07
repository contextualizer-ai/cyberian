"""Tests for task runner."""

import os
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from cyberian.models import LoopCondition, ParamDefinition, Task
from cyberian.runner import TaskRunner


def test_render_instructions_with_context():
    """Test Jinja2 template rendering with context variables."""
    runner = TaskRunner()

    instructions = "Research {{query}} using {{sources}}"
    context = {"query": "climate change", "sources": "scientific papers"}

    result = runner._render_instructions(instructions, context)

    assert result == "Research climate change using scientific papers"


def test_inject_completion_marker():
    """Test injection of completion status marker."""
    runner = TaskRunner()

    instructions = "Do something"
    result = runner._inject_completion_marker(instructions)

    assert "COMPLETION_STATUS: COMPLETE" in result
    assert "COMPLETION_STATUS: ERROR" in result
    assert result.startswith("Do something")


def test_inject_loop_condition():
    """Test injection of loop condition message."""
    runner = TaskRunner()

    instructions = "Keep researching"
    loop_cond = LoopCondition(
        status="NO_MORE_RESEARCH",
        message="If exhausted, yield status NO_MORE_RESEARCH"
    )

    result = runner._inject_loop_condition(instructions, loop_cond)

    assert "If exhausted, yield status NO_MORE_RESEARCH" in result
    assert result.startswith("Keep researching")


def test_check_completion_status_complete():
    """Test that COMPLETE status passes without error."""
    runner = TaskRunner()

    response = "Here is the result.\n\nCOMPLETION_STATUS: COMPLETE"

    # Should not raise
    runner._check_completion_status(response)


def test_check_completion_status_error():
    """Test that ERROR status raises exception."""
    runner = TaskRunner()

    response = "Something went wrong.\n\nCOMPLETION_STATUS: ERROR"

    with pytest.raises(RuntimeError, match="Task execution failed"):
        runner._check_completion_status(response)


def test_check_completion_status_missing():
    """Test that missing status marker doesn't raise (lenient)."""
    runner = TaskRunner()

    response = "Task completed but no status marker"

    # Should not raise (lenient approach)
    runner._check_completion_status(response)


def test_check_loop_status_found():
    """Test loop status detection when status is present."""
    runner = TaskRunner()

    response = "Research complete. NO_MORE_RESEARCH"

    assert runner._check_loop_status(response, "NO_MORE_RESEARCH") is True


def test_check_loop_status_not_found():
    """Test loop status detection when status is absent."""
    runner = TaskRunner()

    response = "Still researching, need more sources"

    assert runner._check_loop_status(response, "NO_MORE_RESEARCH") is False


def test_check_loop_status_case_insensitive():
    """Test loop status detection is case insensitive."""
    runner = TaskRunner()

    response = "All done. no_more_research here."

    assert runner._check_loop_status(response, "NO_MORE_RESEARCH") is True


def test_send_and_wait_success():
    """Test sending message and waiting for stable status."""
    runner = TaskRunner(timeout=10)

    with patch("cyberian.runner.httpx.post") as mock_post, \
         patch("cyberian.runner.httpx.get") as mock_get, \
         patch("cyberian.runner.time.sleep"):

        # Mock message post
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_post_response

        # Mock status check (stable immediately)
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {"status": "idle"}

        # Mock messages response
        mock_messages_response = Mock()
        mock_messages_response.status_code = 200
        mock_messages_response.json.return_value = {
            "messages": [
                {"content": "User message", "role": "user"},
                {"content": "Agent response", "role": "agent"}
            ]
        }

        mock_get.side_effect = [mock_status_response, mock_messages_response]

        result = runner._send_and_wait("Test instructions")

        assert result == "Agent response"
        mock_post.assert_called_once()


def test_send_and_wait_timeout():
    """Test that timeout is raised when agent doesn't respond."""
    runner = TaskRunner(timeout=5)

    with patch("cyberian.runner.httpx.post") as mock_post, \
         patch("cyberian.runner.httpx.get") as mock_get, \
         patch("cyberian.runner.time.sleep"), \
         patch("cyberian.runner.time.time") as mock_time:

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        # Always return processing status
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {"status": "processing"}
        mock_get.return_value = mock_status_response

        # Simulate time passing - need more values for logging calls
        # Using a counter to return incrementing time values
        time_counter = [0]
        def time_generator():
            time_counter[0] += 0.5
            return time_counter[0]

        mock_time.side_effect = time_generator

        with pytest.raises(TimeoutError, match="did not complete within"):
            runner._send_and_wait("Test")


def test_run_single_task():
    """Test running a single non-looping task."""
    runner = TaskRunner()

    task = Task(
        instructions="Research {{topic}}",
        subtasks={}
    )
    context = {"topic": "AI"}

    with patch.object(runner, "_send_and_wait") as mock_send:
        mock_send.return_value = "Research complete. COMPLETION_STATUS: COMPLETE"

        runner._run_single_task(task, context)

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        assert "Research AI" in call_args
        assert "COMPLETION_STATUS" in call_args


def test_run_looping_task_single_iteration():
    """Test looping task that exits after one iteration."""
    runner = TaskRunner()

    task = Task(
        instructions="Keep researching {{topic}}",
        loop_until=LoopCondition(
            status="DONE",
            message="When finished, say DONE"
        )
    )
    context = {"topic": "ML"}

    with patch.object(runner, "_send_and_wait") as mock_send:
        mock_send.return_value = "All complete. DONE. COMPLETION_STATUS: COMPLETE"

        runner._run_looping_task(task, context)

        # Should only call once because DONE is found
        mock_send.assert_called_once()


def test_run_looping_task_multiple_iterations():
    """Test looping task that runs multiple times."""
    runner = TaskRunner()

    task = Task(
        instructions="Keep researching {{topic}}",
        loop_until=LoopCondition(
            status="DONE",
            message="When finished, say DONE"
        )
    )
    context = {"topic": "ML"}

    responses = [
        "Still working. COMPLETION_STATUS: COMPLETE",
        "More progress. COMPLETION_STATUS: COMPLETE",
        "All done. DONE. COMPLETION_STATUS: COMPLETE"
    ]

    with patch.object(runner, "_send_and_wait") as mock_send:
        mock_send.side_effect = responses

        runner._run_looping_task(task, context)

        # Should call 3 times
        assert mock_send.call_count == 3


def test_run_task_with_subtasks():
    """Test task with multiple subtasks executes in order."""
    runner = TaskRunner()

    task = Task(
        name="parent",
        subtasks={
            "task1": Task(instructions="Do task 1"),
            "task2": Task(instructions="Do task 2"),
            "task3": Task(instructions="Do task 3")
        }
    )
    context = {}

    call_order = []

    def mock_run_single(t, c, s=None):
        call_order.append(t.instructions)

    with patch.object(runner, "_run_single_task", side_effect=mock_run_single):
        runner.run_task(task, context)

    assert call_order == ["Do task 1", "Do task 2", "Do task 3"]


def test_run_task_nested_subtasks():
    """Test deeply nested subtasks execute correctly."""
    runner = TaskRunner()

    task = Task(
        subtasks={
            "level1": Task(
                instructions="Level 1",
                subtasks={
                    "level2": Task(
                        instructions="Level 2",
                        subtasks={
                            "level3": Task(instructions="Level 3")
                        }
                    )
                }
            )
        }
    )
    context = {}

    call_order = []

    def mock_run_single(t, c, s=None):
        call_order.append(t.instructions)

    with patch.object(runner, "_run_single_task", side_effect=mock_run_single):
        runner.run_task(task, context)

    assert call_order == ["Level 1", "Level 2", "Level 3"]


def test_run_task_no_instructions():
    """Test task with no instructions only executes subtasks."""
    runner = TaskRunner()

    task = Task(
        name="parent",
        instructions=None,
        subtasks={
            "child": Task(instructions="Child task")
        }
    )
    context = {}

    with patch.object(runner, "_run_single_task") as mock_run:
        runner.run_task(task, context)

        # Should only call for child, not parent
        mock_run.assert_called_once()


@pytest.mark.parametrize(
    "instructions,context,expected",
    [
        ("Hello {{name}}", {"name": "World"}, "Hello World"),
        ("{{a}} + {{b}} = {{c}}", {"a": "1", "b": "2", "c": "3"}, "1 + 2 = 3"),
        ("No variables", {}, "No variables"),
    ]
)
def test_render_instructions_parametrized(instructions, context, expected):
    """Parametrized test for template rendering."""
    runner = TaskRunner()

    result = runner._render_instructions(instructions, context)

    assert result == expected


def test_integration_with_deep_research_yaml():
    """Integration test with actual deep-research.yaml structure."""
    runner = TaskRunner()

    task = Task(
        name="deep-research",
        description="iteratively does deep research",
        requires_workdir=True,
        params={
            "query": ParamDefinition(range="string", required=True)
        },
        subtasks={
            "initial_search": Task(
                instructions="perform deep research on {{query}}. Write a research plan."
            ),
            "iterate": Task(
                instructions="Keep on researching {{query}}",
                loop_until=LoopCondition(
                    status="NO_MORE_RESEARCH",
                    message="If you think all research avenues are exhausted, yield NO_MORE_RESEARCH"
                )
            )
        }
    )

    context = {"query": "climate change"}

    responses = [
        "Research plan created. COMPLETION_STATUS: COMPLETE",  # initial_search
        "More research done. COMPLETION_STATUS: COMPLETE",     # iterate loop 1
        "Final research. NO_MORE_RESEARCH. COMPLETION_STATUS: COMPLETE"  # iterate loop 2
    ]

    with patch.object(runner, "_send_and_wait") as mock_send:
        mock_send.side_effect = responses

        runner.run_task(task, context)

        # Should be called 3 times total
        assert mock_send.call_count == 3

        # Verify template rendering worked
        first_call = mock_send.call_args_list[0][0][0]
        assert "climate change" in first_call


def test_resume_from_skips_early_tasks():
    """Test that resume_from skips tasks before the resume point."""
    runner = TaskRunner(resume_from="task2")

    task = Task(
        name="parent",
        subtasks={
            "task1": Task(name="task1", instructions="Do task 1"),
            "task2": Task(name="task2", instructions="Do task 2"),
            "task3": Task(name="task3", instructions="Do task 3")
        }
    )
    context = {}

    executed_tasks = []

    def mock_run_single(t, c, s=None):
        executed_tasks.append(t.instructions)

    with patch.object(runner, "_run_single_task", side_effect=mock_run_single):
        runner.run_task(task, context)

    # Should skip task1, execute task2 and task3
    assert executed_tasks == ["Do task 2", "Do task 3"]


def test_resume_from_executes_from_resume_point():
    """Test that resume_from executes the resume task and all after."""
    runner = TaskRunner(resume_from="iterate")

    task = Task(
        name="deep-research",
        subtasks={
            "initial_search": Task(name="initial_search", instructions="Initial search"),
            "iterate": Task(name="iterate", instructions="Iterate research"),
            "finalize": Task(name="finalize", instructions="Finalize report")
        }
    )
    context = {}

    executed_tasks = []

    def mock_run_single(t, c, s=None):
        executed_tasks.append(t.instructions)

    with patch.object(runner, "_run_single_task", side_effect=mock_run_single):
        runner.run_task(task, context)

    # Should skip initial_search, execute iterate and finalize
    assert executed_tasks == ["Iterate research", "Finalize report"]


def test_resume_from_nested_subtask():
    """Test resume_from works with nested subtasks."""
    runner = TaskRunner(resume_from="nested_task")

    task = Task(
        name="parent",
        subtasks={
            "task1": Task(
                name="task1",
                instructions="Task 1",
                subtasks={
                    "nested_task": Task(name="nested_task", instructions="Nested task")
                }
            ),
            "task2": Task(name="task2", instructions="Task 2")
        }
    )
    context = {}

    executed_tasks = []

    def mock_run_single(t, c, s=None):
        executed_tasks.append(t.instructions)

    with patch.object(runner, "_run_single_task", side_effect=mock_run_single):
        runner.run_task(task, context)

    # Should find nested_task and execute it plus task2
    assert executed_tasks == ["Nested task", "Task 2"]


def test_no_resume_executes_all_tasks():
    """Test that without resume_from, all tasks execute."""
    runner = TaskRunner()  # No resume_from

    task = Task(
        name="parent",
        subtasks={
            "task1": Task(name="task1", instructions="Do task 1"),
            "task2": Task(name="task2", instructions="Do task 2"),
            "task3": Task(name="task3", instructions="Do task 3")
        }
    )
    context = {}

    executed_tasks = []

    def mock_run_single(t, c, s=None):
        executed_tasks.append(t.instructions)

    with patch.object(runner, "_run_single_task", side_effect=mock_run_single):
        runner.run_task(task, context)

    # Should execute all tasks
    assert executed_tasks == ["Do task 1", "Do task 2", "Do task 3"]


def test_check_success_criteria_passes():
    """Test that success criteria passes when result = True."""
    from cyberian.models import SuccessCriteria

    runner = TaskRunner()

    criteria = SuccessCriteria(python="result = True")

    success, error = runner._check_success_criteria(criteria, {})
    assert success is True
    assert error is None


def test_check_success_criteria_fails():
    """Test that success criteria fails when result = False."""
    from cyberian.models import SuccessCriteria

    runner = TaskRunner()

    criteria = SuccessCriteria(python="result = False")

    success, error = runner._check_success_criteria(criteria, {})
    assert success is False
    assert "validation failed: result = False" in error


def test_check_success_criteria_no_result_variable():
    """Test that error is returned when no result variable is set."""
    from cyberian.models import SuccessCriteria

    runner = TaskRunner()

    criteria = SuccessCriteria(python="x = 5")  # No result variable

    success, error = runner._check_success_criteria(criteria, {})
    assert success is False
    assert "did not set 'result' variable" in error


def test_check_success_criteria_result_not_bool():
    """Test that error is returned when result is not a boolean."""
    from cyberian.models import SuccessCriteria

    runner = TaskRunner()

    criteria = SuccessCriteria(python="result = 42")  # Not a bool

    success, error = runner._check_success_criteria(criteria, {})
    assert success is False
    assert "result must be bool" in error


def test_check_success_criteria_execution_error():
    """Test that execution errors are caught and reported."""
    from cyberian.models import SuccessCriteria

    runner = TaskRunner()

    criteria = SuccessCriteria(python="result = 1 / 0")  # Division by zero

    success, error = runner._check_success_criteria(criteria, {})
    assert success is False
    assert "Error executing success criteria" in error


def test_check_success_criteria_with_file_check(tmp_path):
    """Test success criteria that checks file length."""
    from cyberian.models import SuccessCriteria
    import os

    runner = TaskRunner()

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")

    # Change to tmp directory so the code can find the file
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        criteria = SuccessCriteria(
            python="""
with open('test.txt', 'r') as f:
    content = f.read()
result = len(content) <= 20
"""
        )

        # Should pass (13 chars <= 20)
        success, error = runner._check_success_criteria(criteria, {})
        assert success is True
        assert error is None

        # Now test failure case
        criteria_fail = SuccessCriteria(
            python="""
with open('test.txt', 'r') as f:
    content = f.read()
result = len(content) <= 5
"""
        )

        success, error = runner._check_success_criteria(criteria_fail, {})
        assert success is False
        assert "validation failed" in error
    finally:
        os.chdir(original_cwd)


def test_check_success_criteria_with_template_variables(tmp_path):
    """Test success criteria with Jinja2 template variables."""
    from cyberian.models import SuccessCriteria
    import os

    runner = TaskRunner()

    # Create a test file
    test_file = tmp_path / "output.txt"
    test_file.write_text("Hello, world!")

    # Change to tmp directory
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Success criteria using template variable
        criteria = SuccessCriteria(
            python="""
with open('output.txt', 'r') as f:
    content = f.read()
result = len(content) <= {{max_length}}
"""
        )

        context = {"max_length": 20}

        # Should pass (13 chars <= 20)
        success, error = runner._check_success_criteria(criteria, context)
        assert success is True
        assert error is None

        # Now test with smaller limit - should fail
        context_fail = {"max_length": 5}
        success, error = runner._check_success_criteria(criteria, context_fail)
        assert success is False
        assert "validation failed" in error
    finally:
        os.chdir(original_cwd)


def test_success_criteria_retry_passes_on_second_attempt(tmp_path):
    """Test that success criteria retries work and pass on second attempt."""
    from cyberian.models import SuccessCriteria, Task

    runner = TaskRunner()

    # Create a counter file to track attempts
    counter_file = tmp_path / "attempt_counter.txt"
    counter_file.write_text("0")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Create a task that fails first time, succeeds second time
        task = Task(
            name="test_retry",
            instructions="Try to do the task",
            success_criteria=SuccessCriteria(
                python="""
with open('attempt_counter.txt', 'r') as f:
    count = int(f.read())
count += 1
with open('attempt_counter.txt', 'w') as f:
    f.write(str(count))
result = count >= 2  # Fail on first attempt, pass on second
""",
                max_retries=2,
                retry_message="Validation failed with error: {{error}}. Please try again."
            )
        )

        # Mock _send_and_wait to simulate agent responses
        call_count = 0

        def mock_send_and_wait(content):
            nonlocal call_count
            call_count += 1
            return "COMPLETION_STATUS: COMPLETE"

        with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
            runner.run_task(task, {})

        # Should have been called twice (initial + 1 retry)
        assert call_count == 2
        # Final counter should be 2
        assert counter_file.read_text() == "2"
    finally:
        os.chdir(original_cwd)


def test_success_criteria_retry_fails_after_max_retries(tmp_path):
    """Test that task fails after exhausting max_retries."""
    from cyberian.models import SuccessCriteria, Task

    runner = TaskRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        task = Task(
            name="test_retry_fail",
            instructions="Try to do the task",
            success_criteria=SuccessCriteria(
                python="result = False",  # Always fails
                max_retries=2,
                retry_message="Try again, you failed!"
            )
        )

        call_count = 0

        def mock_send_and_wait(content):
            nonlocal call_count
            call_count += 1
            return "COMPLETION_STATUS: COMPLETE"

        with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
            with pytest.raises(RuntimeError, match="Success criteria validation failed"):
                runner.run_task(task, {})

        # Should have been called 3 times (initial + 2 retries)
        assert call_count == 3
    finally:
        os.chdir(original_cwd)


def test_success_criteria_retry_message_includes_error():
    """Test that retry_message includes error details."""
    from cyberian.models import SuccessCriteria, Task

    runner = TaskRunner()

    task = Task(
        name="test",
        instructions="Do something",
        success_criteria=SuccessCriteria(
            python="result = False",
            max_retries=1,
            retry_message="Previous error was: {{error}}"
        )
    )

    received_messages = []

    def mock_send_and_wait(content):
        received_messages.append(content)
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        with pytest.raises(RuntimeError):
            runner.run_task(task, {})

    # Check that second message contains retry_message with error
    assert len(received_messages) == 2
    assert "Previous error was:" in received_messages[1]
    assert "validation failed" in received_messages[1]


def test_success_criteria_no_retry_fails_immediately(tmp_path):
    """Test that without max_retries, task fails immediately (backward compatible)."""
    from cyberian.models import SuccessCriteria, Task

    runner = TaskRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        task = Task(
            name="test",
            instructions="Do something",
            success_criteria=SuccessCriteria(
                python="result = False"
                # No max_retries specified (defaults to 0)
            )
        )

        call_count = 0

        def mock_send_and_wait(content):
            nonlocal call_count
            call_count += 1
            return "COMPLETION_STATUS: COMPLETE"

        with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
            with pytest.raises(RuntimeError, match="Success criteria validation failed"):
                runner.run_task(task, {})

        # Should have been called only once (no retries)
        assert call_count == 1
    finally:
        os.chdir(original_cwd)


def test_success_criteria_retry_with_looping_task(tmp_path):
    """Test that success_criteria retries work with looping tasks."""
    from cyberian.models import LoopCondition, SuccessCriteria, Task

    runner = TaskRunner()

    # Create a counter to track loop iterations and validation attempts
    counter_file = tmp_path / "validation_counter.txt"
    counter_file.write_text("0")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        task = Task(
            name="test_loop_retry",
            instructions="Do iteration",
            loop_until=LoopCondition(
                status="DONE",
                message="Print DONE when finished"
            ),
            success_criteria=SuccessCriteria(
                python="""
with open('validation_counter.txt', 'r') as f:
    count = int(f.read())
count += 1
with open('validation_counter.txt', 'w') as f:
    f.write(str(count))
result = count >= 2  # Fail first validation, pass second
""",
                max_retries=2,
                retry_message="Validation failed, retrying entire loop"
            )
        )

        loop_iteration_count = 0
        loop_attempts = []

        def mock_send_and_wait(content):
            nonlocal loop_iteration_count
            loop_iteration_count += 1
            loop_attempts.append(loop_iteration_count)
            # Complete loop after 2 iterations within each attempt
            # Check if we're in iteration 2, 3, or higher
            # For simplicity, just signal DONE on every 2nd call
            if loop_iteration_count % 2 == 0 or loop_iteration_count >= 3:
                return "DONE\nCOMPLETION_STATUS: COMPLETE"
            return "COMPLETION_STATUS: COMPLETE"

        with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
            runner.run_task(task, {})

        # First attempt: 2 loop iterations (validation fails)
        # Second attempt: 1 loop iteration completes immediately (validation passes)
        # Total: 3 iterations
        assert loop_iteration_count == 3
        assert counter_file.read_text() == "2"
    finally:
        os.chdir(original_cwd)


def test_system_instructions_inherited_by_subtasks():
    """Test that system_instructions are inherited from parent to child tasks."""
    runner = TaskRunner()

    task = Task(
        name="parent",
        system_instructions="SYSTEM: Use {{mode}} mode",
        subtasks={
            "child1": Task(instructions="Do task 1"),
            "child2": Task(instructions="Do task 2")
        }
    )
    context = {"mode": "verbose"}

    received_instructions = []

    def mock_send_and_wait(content):
        received_instructions.append(content)
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        runner.run_task(task, context)

    # Both subtasks should receive system instructions
    assert len(received_instructions) == 2
    assert "SYSTEM: Use verbose mode" in received_instructions[0]
    assert "Do task 1" in received_instructions[0]
    assert "SYSTEM: Use verbose mode" in received_instructions[1]
    assert "Do task 2" in received_instructions[1]


def test_system_instructions_child_overrides_parent():
    """Test that child tasks can override parent's system_instructions."""
    runner = TaskRunner()

    task = Task(
        name="parent",
        system_instructions="PARENT SYSTEM",
        subtasks={
            "child1": Task(
                instructions="Do task 1",
                system_instructions="CHILD OVERRIDE"
            ),
            "child2": Task(instructions="Do task 2")  # Inherits parent
        }
    )
    context = {}

    received_instructions = []

    def mock_send_and_wait(content):
        received_instructions.append(content)
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        runner.run_task(task, context)

    # child1 should have overridden system instructions
    assert "CHILD OVERRIDE" in received_instructions[0]
    assert "PARENT SYSTEM" not in received_instructions[0]

    # child2 should inherit parent's system instructions
    assert "PARENT SYSTEM" in received_instructions[1]
    assert "CHILD OVERRIDE" not in received_instructions[1]


def test_system_instructions_jinja2_rendering():
    """Test that system_instructions support Jinja2 templating."""
    runner = TaskRunner()

    task = Task(
        name="test",
        system_instructions="Use {{agent}} with {{verbosity}} verbosity",
        instructions="Do the task"
    )
    context = {"agent": "Claude", "verbosity": "high"}

    received_content = None

    def mock_send_and_wait(content):
        nonlocal received_content
        received_content = content
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        runner.run_task(task, context)

    # Check that template variables were rendered
    assert "Use Claude with high verbosity" in received_content
    assert "Do the task" in received_content


def test_system_instructions_prepended_to_task_instructions():
    """Test that system instructions appear before task instructions."""
    runner = TaskRunner()

    task = Task(
        name="test",
        system_instructions="SYSTEM FIRST",
        instructions="TASK SECOND"
    )
    context = {}

    received_content = None

    def mock_send_and_wait(content):
        nonlocal received_content
        received_content = content
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        runner.run_task(task, context)

    # System instructions should come before task instructions
    system_idx = received_content.index("SYSTEM FIRST")
    task_idx = received_content.index("TASK SECOND")
    assert system_idx < task_idx


def test_system_instructions_with_looping_task():
    """Test that system_instructions work with looping tasks."""
    runner = TaskRunner()

    loop_condition = LoopCondition(
        status="DONE",
        message="Print DONE when finished"
    )

    task = Task(
        name="looping",
        system_instructions="LOOP SYSTEM: {{context_var}}",
        instructions="Do iteration",
        loop_until=loop_condition
    )
    context = {"context_var": "test_value"}

    iteration_count = 0

    def mock_send_and_wait(content):
        nonlocal iteration_count
        iteration_count += 1
        # Check system instructions are present
        assert "LOOP SYSTEM: test_value" in content
        assert "Do iteration" in content
        # Exit after 2 iterations
        if iteration_count >= 2:
            return "DONE\nCOMPLETION_STATUS: COMPLETE"
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        runner.run_task(task, context)

    assert iteration_count == 2  # Loop should run twice


def test_system_instructions_none_skips_injection():
    """Test that when system_instructions is None, no injection occurs."""
    runner = TaskRunner()

    task = Task(
        name="test",
        system_instructions=None,
        instructions="Just the task"
    )
    context = {}

    received_content = None

    def mock_send_and_wait(content):
        nonlocal received_content
        received_content = content
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        runner.run_task(task, context)

    # Should only contain task instructions and completion marker
    assert "Just the task" in received_content
    assert "COMPLETION_STATUS" in received_content
    # Should not have any system prefix
    lines = received_content.split('\n')
    assert lines[0].startswith("Just the task") or "Just the task" in lines[0]


# ============================================================================
# Agent Lifecycle Tests
# ============================================================================

def test_lifecycle_reuse_mode_default():
    """Test that REUSE mode (default) does not manage server."""
    runner = TaskRunner(host="localhost", port=3284)

    # Default should be reuse
    assert runner.lifecycle_mode == "reuse"

    task = Task(
        name="test",
        instructions="Do something"
    )
    context = {}

    start_call_count = 0
    stop_call_count = 0

    def mock_start():
        nonlocal start_call_count
        start_call_count += 1

    def mock_stop():
        nonlocal stop_call_count
        stop_call_count += 1

    def mock_send_and_wait(content):
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_start_server", side_effect=mock_start):
        with patch.object(runner, "_stop_server", side_effect=mock_stop):
            with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
                runner.run_task(task, context)

    # In REUSE mode, server should not be managed
    assert start_call_count == 0
    assert stop_call_count == 0


def test_lifecycle_refresh_mode_restarts_server():
    """Test that REFRESH mode restarts server before tasks with instructions."""
    runner = TaskRunner(
        host="localhost",
        port=3284,
        lifecycle_mode="refresh",
        agent_type="claude",
        skip_permissions=True
    )

    task = Task(
        name="test",
        subtasks={
            "step1": Task(instructions="First task"),
            "step2": Task(instructions="Second task"),
            "step3": Task(instructions="Third task")
        }
    )
    context = {}

    start_calls = []
    stop_calls = []

    def mock_start():
        start_calls.append(True)
        # Simulate server process being set
        runner._server_process = "mock_process"

    def mock_stop():
        stop_calls.append(True)
        # Simulate server process being cleared
        runner._server_process = None

    def mock_send_and_wait(content):
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_start_server", side_effect=mock_start):
        with patch.object(runner, "_stop_server", side_effect=mock_stop):
            with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
                runner.run_task(task, context)

    # Server should be started once for each subtask with instructions (3 times)
    assert len(start_calls) == 3
    # Server should be stopped before 2nd and 3rd task (2 times total)
    # First task: start (no stop)
    # Second task: stop, start
    # Third task: stop, start
    assert len(stop_calls) == 2


def test_lifecycle_refresh_skips_tasks_without_instructions():
    """Test that REFRESH mode does not restart for container tasks (no instructions)."""
    runner = TaskRunner(
        host="localhost",
        port=3284,
        lifecycle_mode="refresh",
        agent_type="claude"
    )

    task = Task(
        name="test",
        subtasks={
            "container": Task(  # No instructions - just a container
                subtasks={
                    "step1": Task(instructions="First task"),
                    "step2": Task(instructions="Second task")
                }
            )
        }
    )
    context = {}

    start_calls = []

    def mock_start():
        start_calls.append(True)

    def mock_send_and_wait(content):
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_start_server", side_effect=mock_start):
        with patch.object(runner, "_stop_server"):
            with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
                runner.run_task(task, context)

    # Server should be started only for step1 and step2 (not for "container" or "test")
    assert len(start_calls) == 2


def test_lifecycle_refresh_requires_agent_type():
    """Test that REFRESH mode raises error when agent_type is missing."""
    runner = TaskRunner(
        host="localhost",
        port=3284,
        lifecycle_mode="refresh"
        # No agent_type provided!
    )

    task = Task(
        name="test",
        instructions="Do something"
    )
    context = {}

    def mock_send_and_wait(content):
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
        with pytest.raises(RuntimeError) as exc_info:
            runner.run_task(task, context)

    assert "agent_type not specified" in str(exc_info.value)


def test_lifecycle_refresh_with_server_already_running():
    """Test that REFRESH mode stops existing server before starting new one."""
    runner = TaskRunner(
        host="localhost",
        port=3284,
        lifecycle_mode="refresh",
        agent_type="claude"
    )

    # Simulate an already running server
    runner._server_process = "mock_process"

    task = Task(
        name="test",
        instructions="Do something"
    )
    context = {}

    stop_called = False
    start_called = False

    def mock_stop():
        nonlocal stop_called
        stop_called = True
        runner._server_process = None  # Simulate cleanup

    def mock_start():
        nonlocal start_called
        start_called = True

    def mock_send_and_wait(content):
        return "COMPLETION_STATUS: COMPLETE"

    with patch.object(runner, "_stop_server", side_effect=mock_stop):
        with patch.object(runner, "_start_server", side_effect=mock_start):
            with patch.object(runner, "_send_and_wait", side_effect=mock_send_and_wait):
                runner.run_task(task, context)

    # Both stop and start should be called
    assert stop_called
    assert start_called


def test_server_management_methods():
    """Test server management methods (_start_server, _stop_server, _wait_for_server_ready)."""
    runner = TaskRunner(
        host="localhost",
        port=3284,
        agent_type="claude",
        skip_permissions=True
    )

    # Test _start_server
    mock_process = MagicMock()
    mock_process.pid = 12345

    with patch("subprocess.Popen", return_value=mock_process):
        with patch.object(runner, "_wait_for_server_ready"):
            runner._start_server()

    assert runner._server_process == mock_process

    # Test _stop_server
    runner._stop_server()

    mock_process.terminate.assert_called_once()
    assert runner._server_process is None

    # Test _wait_for_server_ready (successful case)
    runner2 = TaskRunner(host="localhost", port=3284)

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.get", return_value=mock_response):
        runner2._wait_for_server_ready(max_wait=5)

    # Should complete without timeout


def test_wait_for_server_ready_timeout():
    """Test that _wait_for_server_ready raises TimeoutError if server doesn't respond."""
    runner = TaskRunner(host="localhost", port=3284)

    # Mock httpx.get to always raise ConnectError
    with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(TimeoutError) as exc_info:
            runner._wait_for_server_ready(max_wait=1)

    assert "did not become ready" in str(exc_info.value)
