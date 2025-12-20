"""Unit tests for QueueManager retry behavior."""

from unittest.mock import MagicMock, patch

import pika.exceptions
import pytest

from pynenc_rabbitmq.util.rabbitmq_queue import QueueSpec
from pynenc_rabbitmq.util.rabbitmq_queue_mng import QueueManager


@pytest.fixture
def mock_conf() -> MagicMock:
    """Create a mock configuration with retry settings."""
    conf = MagicMock()
    conf.rabbitmq_retry_max_attempts = 3
    conf.rabbitmq_retry_initial_delay = 0.1
    conf.rabbitmq_retry_max_delay = 1.0
    conf.rabbitmq_retry_exponential_base = 2.0
    return conf


@pytest.fixture
def mock_connection_manager(mock_conf: MagicMock) -> MagicMock:
    """Create a mock connection manager."""
    conn_mgr = MagicMock()
    conn_mgr.conf = mock_conf
    return conn_mgr


@pytest.fixture
def queue_spec() -> QueueSpec:
    """Create a test queue spec."""
    return QueueSpec(name="test_queue", durable=True)


@pytest.fixture
def queue_manager(
    mock_connection_manager: MagicMock, queue_spec: QueueSpec
) -> QueueManager:
    """Create a queue manager with mocked dependencies."""
    return QueueManager(mock_connection_manager, queue_spec)


def test_publish_should_retry_on_connection_error(
    queue_manager: QueueManager, mock_connection_manager: MagicMock
) -> None:
    """Should retry publish_message on connection errors."""
    mock_channel = MagicMock()
    attempts = []

    # Create a context manager that fails first time, succeeds second
    def create_context_manager() -> MagicMock:
        cm = MagicMock()
        attempts.append(1)
        if len(attempts) == 1:
            cm.__enter__ = MagicMock(side_effect=pika.exceptions.AMQPConnectionError())
        else:
            cm.__enter__ = MagicMock(return_value=mock_channel)
        cm.__exit__ = MagicMock(return_value=False)
        return cm

    mock_connection_manager.get_channel.side_effect = create_context_manager

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        result = queue_manager.publish_message("test message")

    assert result is True
    assert len(attempts) == 2


def test_consume_should_retry_on_stream_lost(
    queue_manager: QueueManager, mock_connection_manager: MagicMock
) -> None:
    """Should retry consume_message on StreamLostError."""
    mock_channel = MagicMock()
    mock_channel.basic_get.return_value = (MagicMock(), None, b"message")
    attempts = []

    def create_context_manager() -> MagicMock:
        cm = MagicMock()
        attempts.append(1)
        if len(attempts) == 1:
            cm.__enter__ = MagicMock(
                side_effect=pika.exceptions.StreamLostError("lost")
            )
        else:
            cm.__enter__ = MagicMock(return_value=mock_channel)
        cm.__exit__ = MagicMock(return_value=False)
        return cm

    mock_connection_manager.get_channel.side_effect = create_context_manager

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        result = queue_manager.consume_message()

    assert result == "message"
    assert len(attempts) == 2


def test_publish_should_respect_max_attempts(
    mock_connection_manager: MagicMock,
) -> None:
    """Should stop retrying after max_attempts."""
    mock_connection_manager.conf.rabbitmq_retry_max_attempts = 3
    mock_connection_manager.conf.rabbitmq_retry_initial_delay = 0.1
    mock_connection_manager.conf.rabbitmq_retry_max_delay = 1.0
    mock_connection_manager.conf.rabbitmq_retry_exponential_base = 2.0

    spec = QueueSpec(name="test_queue", durable=True)
    queue_manager = QueueManager(mock_connection_manager, spec)

    # Always fail with connection error
    cm = MagicMock()
    cm.__enter__ = MagicMock(side_effect=pika.exceptions.AMQPConnectionError())
    cm.__exit__ = MagicMock(return_value=False)
    mock_connection_manager.get_channel.return_value = cm

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        with pytest.raises(pika.exceptions.AMQPConnectionError):
            queue_manager.publish_message("test")

    # Should have attempted 3 times
    assert mock_connection_manager.get_channel.call_count == 3


def test_purge_should_return_message_count(
    queue_manager: QueueManager, mock_connection_manager: MagicMock
) -> None:
    """Should return number of purged messages."""
    mock_channel = MagicMock()
    mock_result = MagicMock()
    mock_result.method.message_count = 5
    mock_channel.queue_purge.return_value = mock_result

    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_channel)
    cm.__exit__ = MagicMock(return_value=False)
    mock_connection_manager.get_channel.return_value = cm

    result = queue_manager.purge_queue()

    assert result == 5
