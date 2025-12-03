"""Tests for agent_client module."""

from unittest.mock import Mock, patch
import pytest
import httpx
from cyberian.agent_client import (
    get_agent_status,
    get_agent_messages,
    send_agent_message,
    send_message_and_wait,
)


def test_get_agent_status_success():
    """Test getting status from agentapi server.

    >>> with patch('httpx.get') as mock_get:
    ...     mock_response = Mock()
    ...     mock_response.status_code = 200
    ...     mock_response.json.return_value = {"status": "idle", "timestamp": "2025-01-01T00:00:00"}
    ...     mock_get.return_value = mock_response
    ...     status = get_agent_status(4800)
    ...     status['status']
    'idle'
    """
    with patch('httpx.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "idle", "timestamp": "2025-01-01T00:00:00"}
        mock_get.return_value = mock_response

        status = get_agent_status(4800)

        assert status['status'] == 'idle'
        mock_get.assert_called_once_with("http://localhost:4800/status", timeout=2.0)


def test_get_agent_status_custom_host():
    """Test getting status with custom host."""
    with patch('httpx.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ready"}
        mock_get.return_value = mock_response

        get_agent_status(4800, host="example.com", timeout=5.0)

        mock_get.assert_called_once_with("http://example.com:4800/status", timeout=5.0)


def test_get_agent_status_http_error():
    """Test handling of HTTP errors."""
    with patch('httpx.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            get_agent_status(4800)


def test_get_agent_messages_success():
    """Test getting messages from agentapi server.

    >>> with patch('httpx.get') as mock_get:
    ...     mock_response = Mock()
    ...     mock_response.json.return_value = {"messages": [{"role": "user", "content": "Hello"}]}
    ...     mock_get.return_value = mock_response
    ...     messages = get_agent_messages(4800)
    ...     len(messages)
    1
    """
    with patch('httpx.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
        }
        mock_get.return_value = mock_response

        messages = get_agent_messages(4800)

        assert len(messages) == 2
        assert messages[0]['role'] == 'user'
        assert messages[1]['role'] == 'assistant'
        mock_get.assert_called_once_with(
            "http://localhost:4800/messages",
            params={},
            timeout=5.0
        )


def test_get_agent_messages_with_last():
    """Test getting last N messages."""
    with patch('httpx.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        mock_get.return_value = mock_response

        get_agent_messages(4800, last=10)

        call_args = mock_get.call_args
        assert call_args[1]['params'] == {'last': 10}


def test_get_agent_messages_empty():
    """Test getting messages when none exist."""
    with patch('httpx.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        messages = get_agent_messages(4800)

        assert messages == []


def test_send_agent_message_success():
    """Test sending a message to agentapi server.

    >>> with patch('httpx.post') as mock_post:
    ...     mock_response = Mock()
    ...     mock_response.json.return_value = {"status": "accepted"}
    ...     mock_post.return_value = mock_response
    ...     response = send_agent_message(4800, "Hello, agent!")
    ...     response['status']
    'accepted'
    """
    with patch('httpx.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "accepted"}
        mock_post.return_value = mock_response

        response = send_agent_message(4800, "Hello, agent!")

        assert response['status'] == 'accepted'
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:4800/message"
        assert call_args[1]['headers']['Content-Type'] == 'application/json'


def test_send_agent_message_custom_type():
    """Test sending a message with custom type."""
    with patch('httpx.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        send_agent_message(4800, "Test", msg_type="system")

        call_args = mock_post.call_args
        import json
        payload = json.loads(call_args[1]['content'])
        assert payload['type'] == 'system'


def test_send_agent_message_http_error():
    """Test handling of HTTP errors when sending message."""
    with patch('httpx.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request", request=Mock(), response=mock_response
        )
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            send_agent_message(4800, "Test")


def test_send_message_and_wait_success():
    """Test sending message and waiting for response."""
    with patch('cyberian.agent_client.send_agent_message') as mock_send:
        mock_send.return_value = {"status": "accepted"}

        with patch('httpx.get') as mock_get:
            # First status check: processing
            status_response1 = Mock()
            status_response1.json.return_value = {"status": "processing"}

            # Second status check: idle
            status_response2 = Mock()
            status_response2.json.return_value = {"status": "idle"}

            # Messages response
            messages_response = Mock()
            messages_response.json.return_value = {
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there"}
                ]
            }

            mock_get.side_effect = [status_response1, status_response2, messages_response]

            with patch('time.sleep'):
                response = send_message_and_wait(4800, "Hello", poll_interval=0.1)

            assert response == "Hi there"
            mock_send.assert_called_once_with(4800, "Hello", host="localhost", timeout=30.0)


def test_send_message_and_wait_timeout():
    """Test timeout when waiting for agent response."""
    with patch('cyberian.agent_client.send_agent_message') as mock_send:
        mock_send.return_value = {"status": "accepted"}

        with patch('httpx.get') as mock_get:
            # Always return processing status
            status_response = Mock()
            status_response.json.return_value = {"status": "processing"}
            mock_get.return_value = status_response

            with patch('time.sleep'):
                with patch('time.time', side_effect=[0, 0, 61, 62]):  # Simulate timeout
                    with pytest.raises(TimeoutError, match="Timeout exceeded"):
                        send_message_and_wait(4800, "Hello", timeout=60)


def test_send_message_and_wait_no_agent_response():
    """Test error when no agent response found."""
    with patch('cyberian.agent_client.send_agent_message') as mock_send:
        mock_send.return_value = {"status": "accepted"}

        with patch('httpx.get') as mock_get:
            # Status check: idle
            status_response = Mock()
            status_response.json.return_value = {"status": "idle"}

            # Messages response - only user message
            messages_response = Mock()
            messages_response.json.return_value = {
                "messages": [{"role": "user", "content": "Hello"}]
            }

            mock_get.side_effect = [status_response, messages_response]

            with patch('time.sleep'):
                with pytest.raises(ValueError, match="No agent response found"):
                    send_message_and_wait(4800, "Hello")


def test_send_message_and_wait_multiple_status_states():
    """Test handling of different agent status states."""
    with patch('cyberian.agent_client.send_agent_message') as mock_send:
        with patch('cyberian.agent_client.get_agent_messages') as mock_get_messages:
            mock_send.return_value = {"status": "accepted"}
            mock_get_messages.return_value = [
                {"role": "assistant", "content": "Response"}
            ]

            with patch('httpx.get') as mock_get:
                # Test different terminal states
                for terminal_state in ["idle", "ready", "stable", "waiting"]:
                    status_response = Mock()
                    status_response.json.return_value = {"status": terminal_state}
                    mock_get.return_value = status_response

                    response = send_message_and_wait(4800, "Test", poll_interval=0.1)
                    assert response == "Response"
