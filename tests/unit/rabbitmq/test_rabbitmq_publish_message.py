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

from pynenc_rabbitmq.util.rabbitmq_conn_mng import ConnectionManager
from pynenc_rabbitmq.util.rabbitmq_queue import QueueSpec
from pynenc_rabbitmq.util.rabbitmq_queue_mng import QueueManager


@pytest.fixture
def mock_connection_manager() -> MagicMock:
    """Create a mock connection manager."""
    return MagicMock(spec=ConnectionManager)


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
    mock_connection_manager.get_channel.return_value.__enter__.return_value = (
        mock_channel
    )
    test_message = "some-serialized-invocation"

    # Act
    result = queue_manager.publish_message(test_message)

    # Assert
    assert result is True
    mock_channel.queue_declare.assert_called_once_with(
        queue=queue_spec.name,
        durable=queue_spec.durable,
        exclusive=queue_spec.exclusive,
        auto_delete=queue_spec.auto_delete,
        arguments=queue_spec.arguments,
    )
    mock_channel.basic_publish.assert_called_once()

    # Verify publish arguments
    publish_call = mock_channel.basic_publish.call_args
    assert publish_call.kwargs["exchange"] == queue_spec.exchange
    assert publish_call.kwargs["routing_key"] == queue_spec.routing_key
    assert isinstance(publish_call.kwargs["properties"], pika.BasicProperties)
    assert publish_call.kwargs["properties"].delivery_mode == 2  # Persistent


def test_publish_message_should_use_transient_delivery_when_queue_not_durable() -> None:
    """Test that publish_message uses transient delivery mode for non-durable queues."""
    # Arrange
    mock_conn_mgr = MagicMock()
    mock_channel = MagicMock()
    mock_conn_mgr.get_channel.return_value.__enter__.return_value = mock_channel

    spec = QueueSpec(name="temp_queue", durable=False)
    manager = QueueManager(mock_conn_mgr, spec)

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
    mock_connection_manager.get_channel.side_effect = Exception("Connection failed")

    # Act
    result = queue_manager.publish_message("some-serialized-invocation")

    # Assert
    assert result is False


def test_publish_message_should_handle_channel_error(
    queue_manager: QueueManager, mock_connection_manager: MagicMock
) -> None:
    """Test that publish_message handles channel errors gracefully."""
    # Arrange
    mock_channel = MagicMock()
    mock_channel.basic_publish.side_effect = pika.exceptions.AMQPError("Channel error")
    mock_connection_manager.get_channel.return_value.__enter__.return_value = (
        mock_channel
    )

    # Act
    result = queue_manager.publish_message("data")

    # Assert
    assert result is False


def test_publish_message_should_use_custom_exchange_and_routing_key() -> None:
    """Test that publish_message uses custom exchange and routing key from spec."""
    # Arrange
    mock_conn_mgr = MagicMock()
    mock_channel = MagicMock()
    mock_conn_mgr.get_channel.return_value.__enter__.return_value = mock_channel

    spec = QueueSpec(
        name="test_queue", exchange="custom_exchange", routing_key="custom.routing.key"
    )
    manager = QueueManager(mock_conn_mgr, spec)

    # Act
    manager.publish_message("some-serialized-invocation")

    # Assert
    publish_call = mock_channel.basic_publish.call_args
    assert publish_call.kwargs["exchange"] == "custom_exchange"
    assert publish_call.kwargs["routing_key"] == "custom.routing.key"
