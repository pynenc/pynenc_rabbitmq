"""
Unit tests for RabbitMQ queue manager.

Tests cover:
- Message publishing
- Message consumption
- Queue operations (count, purge)
- Error handling
"""

from unittest.mock import MagicMock

import pika
import pytest

from pynenc_rabbitmq.util.rabbitmq_queue import QueueSpec
from pynenc_rabbitmq.util.rabbitmq_queue_mng import QueueManager


@pytest.fixture
def mock_conf() -> MagicMock:
    """Create mock configuration with retry settings."""
    conf = MagicMock()
    conf.rabbitmq_retry_max_attempts = 1  # Don't retry in these tests
    conf.rabbitmq_retry_initial_delay = 0.1
    conf.rabbitmq_retry_max_delay = 1.0
    conf.rabbitmq_retry_exponential_base = 2.0
    return conf


@pytest.fixture
def mock_connection_manager(mock_conf: MagicMock) -> MagicMock:
    """Create a mock ConnectionManager with conf attribute."""
    mock = MagicMock(spec=["get_channel", "conf"])
    mock.conf = mock_conf
    return mock


@pytest.fixture
def queue_spec() -> QueueSpec:
    """Create a test queue specification."""
    return QueueSpec(
        name="test_queue", durable=True, exchange="", routing_key="test_queue"
    )


@pytest.fixture
def queue_manager(
    mock_connection_manager: MagicMock, queue_spec: QueueSpec
) -> QueueManager:
    """Create a QueueManager instance with mocked dependencies."""
    return QueueManager(mock_connection_manager, queue_spec)


def test_publish_message_should_declare_queue_and_publish(
    queue_manager: QueueManager,
    mock_connection_manager: MagicMock,
    queue_spec: QueueSpec,
) -> None:
    """Test that publish_message declares the queue and publishes the message."""
    # Arrange
    mock_channel = MagicMock()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_channel)
    cm.__exit__ = MagicMock(return_value=False)
    mock_connection_manager.get_channel.return_value = cm
    test_message = "some-serialized-invocation"

    # Act
    result = queue_manager.publish_message(test_message)

    # Assert
    assert result is True
    mock_channel.queue_declare.assert_called_once_with(
        queue=queue_spec.name,
        durable=queue_spec.durable,
    )
    mock_channel.basic_publish.assert_called_once()

    # Verify publish arguments
    publish_call = mock_channel.basic_publish.call_args
    assert publish_call.kwargs["exchange"] == queue_spec.exchange
    assert publish_call.kwargs["routing_key"] == queue_spec.routing_key
    assert isinstance(publish_call.kwargs["properties"], pika.BasicProperties)
    assert publish_call.kwargs["properties"].delivery_mode == 2  # Persistent


def test_publish_message_should_use_transient_delivery_when_queue_not_durable(
    mock_connection_manager: MagicMock,
) -> None:
    """Test that publish_message uses transient delivery mode for non-durable queues."""
    # Arrange
    mock_channel = MagicMock()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_channel)
    cm.__exit__ = MagicMock(return_value=False)
    mock_connection_manager.get_channel.return_value = cm

    spec = QueueSpec(name="temp_queue", durable=False)
    manager = QueueManager(mock_connection_manager, spec)

    # Act
    manager.publish_message("some-serialized-invocation")

    # Assert
    publish_call = mock_channel.basic_publish.call_args
    assert publish_call.kwargs["properties"].delivery_mode == 1  # Transient


def test_publish_message_should_return_false_on_exception(
    queue_manager: QueueManager, mock_connection_manager: MagicMock
) -> None:
    """Test that publish_message returns False when an exception occurs."""
    # Arrange
    mock_channel = MagicMock()
    mock_channel.basic_publish.side_effect = ValueError("Some error")
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_channel)
    cm.__exit__ = MagicMock(return_value=False)
    mock_connection_manager.get_channel.return_value = cm

    # Act
    result = queue_manager.publish_message("some-message")

    # Assert
    assert result is False


def test_publish_message_should_handle_channel_error(
    queue_manager: QueueManager, mock_connection_manager: MagicMock
) -> None:
    """Test that publish_message handles channel errors gracefully."""
    # Arrange - use non-recoverable exception to avoid retry
    mock_channel = MagicMock()
    mock_channel.queue_declare.side_effect = ValueError("Channel error")
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_channel)
    cm.__exit__ = MagicMock(return_value=False)
    mock_connection_manager.get_channel.return_value = cm

    # Act
    result = queue_manager.publish_message("some-message")

    # Assert
    assert result is False


def test_publish_message_should_use_custom_exchange_and_routing_key(
    mock_connection_manager: MagicMock,
) -> None:
    """Test that publish_message uses custom exchange and routing key from spec."""
    # Arrange
    mock_channel = MagicMock()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_channel)
    cm.__exit__ = MagicMock(return_value=False)
    mock_connection_manager.get_channel.return_value = cm

    spec = QueueSpec(
        name="test_queue", exchange="custom_exchange", routing_key="custom.routing.key"
    )
    manager = QueueManager(mock_connection_manager, spec)

    # Act
    manager.publish_message("some-serialized-invocation")

    # Assert
    publish_call = mock_channel.basic_publish.call_args
    assert publish_call.kwargs["exchange"] == "custom_exchange"
    assert publish_call.kwargs["routing_key"] == "custom.routing.key"
