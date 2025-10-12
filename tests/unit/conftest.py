"""
Unit test configuration with mocked RabbitMQ components.

This conftest provides fixtures for unit testing without requiring a real RabbitMQ instance.
All RabbitMQ operations are mocked to enable fast, isolated unit tests.
"""

from collections import deque
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from pynenc import PynencBuilder

from pynenc_rabbitmq.util.rabbitmq_client import PynencRabbitMqClient

if TYPE_CHECKING:
    from collections.abc import Generator

    from pynenc.app import Pynenc


class MockRabbitMqQueue:
    """In-memory mock implementation of RabbitMQ queue for unit testing."""

    def __init__(self) -> None:
        self.messages: deque[dict[str, Any]] = deque()
        self.setup_called = False

    def publish_message(self, message: dict[str, Any]) -> bool:
        """Mock publish message."""
        self.messages.append(message)
        return True

    def consume_message(self) -> dict[str, Any] | None:
        """Mock consume message."""
        return self.messages.popleft() if self.messages else None

    def get_message_count(self) -> int:
        """Mock get message count."""
        return len(self.messages)

    def purge_queue(self) -> int:
        """Mock purge queue."""
        count = len(self.messages)
        self.messages.clear()
        return count


class MockConnectionManager:
    """Mock connection manager for unit testing."""

    def __init__(self, conf: Any) -> None:
        self.conf = conf
        self.closed = False
        self._mock_channel = MagicMock()

    def get_channel(self) -> "MockConnectionManager":
        """Mock context manager for channel."""
        return self

    def __enter__(self) -> MagicMock:
        """Return mock channel on context enter."""
        return self._mock_channel

    def __exit__(self, *args: Any) -> None:
        """Mock context exit."""
        pass

    def close(self) -> None:
        """Mock close connection."""
        self.closed = True


class MockQueueManager:
    """Mock queue manager for unit testing."""

    def __init__(self, connection_manager: Any, spec: Any) -> None:
        self.connection_manager = connection_manager
        self.spec = spec
        self._queue = MockRabbitMqQueue()

    def publish_message(self, message: dict[str, Any]) -> bool:
        """Mock publish message."""
        return self._queue.publish_message(message)

    def consume_message(self) -> dict[str, Any] | None:
        """Mock consume message."""
        return self._queue.consume_message()

    def get_message_count(self) -> int:
        """Mock get message count."""
        return self._queue.get_message_count()

    def purge_queue(self) -> int:
        """Mock purge queue."""
        return self._queue.purge_queue()


@pytest.fixture(autouse=True)
def mock_rabbitmq_components() -> "Generator[None, None, None]":
    """
    Automatically mock RabbitMQ components for all unit tests.

    This fixture patches ConnectionManager and QueueManager to use mock implementations,
    ensuring no real RabbitMQ connection is attempted during unit tests.
    """
    # Clear singleton instances before each test
    PynencRabbitMqClient._instances.clear()

    with (
        patch(
            "pynenc_rabbitmq.util.rabbitmq_client.ConnectionManager",
            MockConnectionManager,
        ),
        patch("pynenc_rabbitmq.util.rabbitmq_client.QueueManager", MockQueueManager),
    ):
        yield

    # Clean up after test
    PynencRabbitMqClient._instances.clear()


@pytest.fixture
def app_instance() -> "Generator['Pynenc', None, None]":
    """
    Provide a Pynenc app instance with mocked RabbitMQ backend for unit tests.

    Uses in-memory mocks for all RabbitMQ operations, ensuring fast and isolated tests.

    :return: Generator yielding a Pynenc app instance with mocked backend
    """
    app = (
        PynencBuilder()
        .rabbitmq_broker(
            host="localhost",
            port=5672,
            username="test",
            password="test",
            queue_prefix="test",
        )
        .build()
    )

    yield app

    # Cleanup
    if hasattr(app, "purge"):
        app.purge()
