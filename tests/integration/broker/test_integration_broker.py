"""
Integration tests for RabbitMQ broker with real container.

Tests basic RabbitMQ operations with a real RabbitMQ container to verify:
- Connection establishment
- Message publishing
- Message consumption
- Queue operations
"""

import time
from typing import TYPE_CHECKING

import pytest

from pynenc_rabbitmq.broker import RabbitMqBroker

if TYPE_CHECKING:
    from pynenc import Pynenc
    from testcontainers.rabbitmq import RabbitMqContainer


def test_rabbitmq_container_is_accessible(
    rabbitmq_container: "RabbitMqContainer",
) -> None:
    """Test that the RabbitMQ container is running and accessible."""
    # Just verify the container exists and has expected attributes
    assert rabbitmq_container is not None
    host_ip = rabbitmq_container.get_container_host_ip()
    assert host_ip is not None and len(host_ip) > 0
    assert int(rabbitmq_container.get_exposed_port(5672)) > 0

    print(
        f"\nContainer accessible at: {host_ip}:{rabbitmq_container.get_exposed_port(5672)}"
    )


def test_rabbitmq_client_can_connect(app_instance: "Pynenc") -> None:
    """Test that the RabbitMQ client can establish a connection."""
    # Get the broker's RabbitMQ client
    broker = app_instance.broker

    # The broker should have a _message_queue attribute (QueueManager)
    assert isinstance(broker, RabbitMqBroker)
    queue_manager = broker._message_queue

    # Try to get a connection through the queue manager
    try:
        with queue_manager._connection_manager.get_channel() as channel:
            assert channel is not None
            print(f"\nSuccessfully opened channel: {channel}")
    except Exception as e:
        pytest.fail(f"Failed to open channel: {e}")


def test_rabbitmq_client_can_publish_and_consume(app_instance: "Pynenc") -> None:
    """Test that we can publish and consume messages."""
    broker = app_instance.broker
    assert isinstance(broker, RabbitMqBroker)
    queue_manager = broker._message_queue

    # Test message
    test_message = "some-data"

    # Publish message
    success = queue_manager.publish_message(test_message)
    assert success, "Failed to publish message"

    # Small delay to ensure message is available
    time.sleep(0.1)

    # Consume message
    consumed_message = queue_manager.consume_message()
    assert consumed_message is not None, "Failed to consume message"
    assert consumed_message == test_message
    print(f"\nSuccessfully published and consumed message: {consumed_message}")


def test_rabbitmq_queue_operations(app_instance: "Pynenc") -> None:
    """Test queue count and purge operations."""
    broker = app_instance.broker
    assert isinstance(broker, RabbitMqBroker)
    queue_manager = broker._message_queue

    # Purge queue first
    initial_purge = queue_manager.purge_queue()
    print(f"\nPurged {initial_purge} messages from queue")

    # Verify empty
    count = queue_manager.get_message_count()
    assert count == 0, f"Queue should be empty but has {count} messages"

    # Publish 3 messages
    for i in range(3):
        success = queue_manager.publish_message(f"message-{i}")
        assert success, f"Failed to publish message {i}"

    # Verify count
    count = queue_manager.get_message_count()
    assert count == 3, f"Expected 3 messages but found {count}"

    # Purge again
    purged = queue_manager.purge_queue()
    assert purged == 3, f"Expected to purge 3 messages but purged {purged}"

    # Verify empty again
    count = queue_manager.get_message_count()
    assert count == 0, f"Queue should be empty but has {count} messages"
    print("\nQueue operations successful")
