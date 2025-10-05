"""
Unit tests for RabbitMQ connection manager.

Tests cover:
- Connection parameter generation
- Connection lifecycle management
- Channel context manager
- Thread safety
"""

from unittest.mock import MagicMock, patch

import pytest

from pynenc_rabbitmq.conf.config_rabbitmq import ConfigRabbitMq
from pynenc_rabbitmq.util.rabbitmq_conn_mng import ConnectionManager


@pytest.fixture
def rabbitmq_config() -> ConfigRabbitMq:
    """Create a test RabbitMQ configuration."""
    return ConfigRabbitMq(
        config_values={
            "rabbitmq_host": "localhost",
            "rabbitmq_port": 5672,
            "rabbitmq_username": "test_user",
            "rabbitmq_password": "test_pass",
            "rabbitmq_virtual_host": "/test",
            "rabbitmq_heartbeat": 600,
            "rabbitmq_connection_attempts": 3,
            "rabbitmq_retry_delay": 2,
            "rabbitmq_confirm_delivery": True,
            "rabbitmq_prefetch_count": 10,
        }
    )


def test_get_connection_parameters_should_build_from_config(
    rabbitmq_config: ConfigRabbitMq,
) -> None:
    """Test that connection parameters are correctly built from configuration."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)

    # Act
    params = manager._get_connection_parameters()

    # Assert
    assert params.host == "localhost"
    assert params.port == 5672
    assert params.virtual_host == "/test"
    assert params.credentials.username == "test_user"
    assert params.credentials.password == "test_pass"
    assert params.heartbeat == 600
    assert params.connection_attempts == 3
    assert params.retry_delay == 2


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_ensure_connection_should_create_new_connection_when_none_exists(
    mock_blocking_connection: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that ensure_connection creates a new connection when none exists."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)
    mock_conn = MagicMock()
    mock_blocking_connection.return_value = mock_conn

    # Act
    connection = manager._ensure_connection()

    # Assert
    assert connection == mock_conn
    mock_blocking_connection.assert_called_once()


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_ensure_connection_should_reuse_existing_open_connection(
    mock_blocking_connection: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that ensure_connection reuses an existing open connection."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)
    mock_conn = MagicMock()
    mock_conn.is_closed = False
    mock_blocking_connection.return_value = mock_conn

    # Act
    connection1 = manager._ensure_connection()
    connection2 = manager._ensure_connection()

    # Assert
    assert connection1 == connection2 == mock_conn
    mock_blocking_connection.assert_called_once()


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_ensure_connection_should_create_new_connection_when_existing_is_closed(
    mock_blocking_connection: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that ensure_connection creates a new connection when existing one is closed."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)
    mock_conn1 = MagicMock()
    mock_conn1.is_closed = True
    mock_conn2 = MagicMock()
    mock_conn2.is_closed = False
    mock_blocking_connection.side_effect = [mock_conn1, mock_conn2]

    # Act
    connection1 = manager._ensure_connection()
    connection2 = manager._ensure_connection()

    # Assert
    assert connection1 == mock_conn1
    assert connection2 == mock_conn2
    assert mock_blocking_connection.call_count == 2


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_get_channel_should_yield_channel_with_confirm_delivery(
    mock_blocking_connection: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that get_channel yields a channel with confirm delivery enabled."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_channel.is_open = True
    mock_conn.channel.return_value = mock_channel
    mock_blocking_connection.return_value = mock_conn

    # Act
    with manager.get_channel() as channel:
        result_channel = channel

    # Assert
    assert result_channel == mock_channel
    mock_channel.confirm_delivery.assert_called_once()
    mock_channel.basic_qos.assert_called_once_with(prefetch_count=10)
    mock_channel.close.assert_called_once()


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_get_channel_should_close_channel_even_on_exception(
    mock_blocking_connection: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that get_channel closes the channel even when an exception occurs."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_channel.is_open = True
    mock_conn.channel.return_value = mock_channel
    mock_blocking_connection.return_value = mock_conn

    # Act & Assert
    with pytest.raises(RuntimeError):
        with manager.get_channel():
            raise RuntimeError("Test error")

    mock_channel.close.assert_called_once()


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_get_channel_should_skip_confirm_delivery_when_disabled(
    mock_blocking_connection: MagicMock,
) -> None:
    """Test that get_channel skips confirm_delivery when disabled in config."""
    # Arrange
    config = ConfigRabbitMq(
        config_values={
            "rabbitmq_confirm_delivery": False,
            "rabbitmq_prefetch_count": 5,
        }
    )
    manager = ConnectionManager(config)
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_channel.is_open = True
    mock_conn.channel.return_value = mock_channel
    mock_blocking_connection.return_value = mock_conn

    # Act
    with manager.get_channel():
        pass

    # Assert
    mock_channel.confirm_delivery.assert_not_called()
    mock_channel.basic_qos.assert_called_once_with(prefetch_count=5)


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_close_should_close_open_connection(
    mock_blocking_connection: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that close properly closes an open connection."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)
    mock_conn = MagicMock()
    mock_conn.is_closed = False
    mock_blocking_connection.return_value = mock_conn
    manager._ensure_connection()

    # Act
    manager.close()

    # Assert
    mock_conn.close.assert_called_once()
    assert manager._local.connection is None


@patch("pynenc_rabbitmq.util.rabbitmq_conn_mng.pika.BlockingConnection")
def test_close_should_handle_already_closed_connection(
    mock_blocking_connection: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that close handles an already closed connection gracefully."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)
    mock_conn = MagicMock()
    mock_conn.is_closed = True
    mock_blocking_connection.return_value = mock_conn
    manager._ensure_connection()

    # Act
    manager.close()

    # Assert
    mock_conn.close.assert_not_called()


def test_close_should_handle_no_connection(rabbitmq_config: ConfigRabbitMq) -> None:
    """Test that close handles the case when no connection exists."""
    # Arrange
    manager = ConnectionManager(rabbitmq_config)

    # Act & Assert (should not raise)
    manager.close()
    assert (
        not hasattr(manager._local, "connection") or manager._local.connection is None
    )
