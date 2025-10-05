"""
Unit tests for RabbitMQ client singleton and connection management.

Tests cover:
- Singleton instance management
- Connection key generation
- Queue manager creation
"""

from unittest.mock import MagicMock, patch

import pytest

from pynenc_rabbitmq.conf.config_rabbitmq import ConfigRabbitMq
from pynenc_rabbitmq.util.rabbitmq_client import PynencRabbitMqClient
from pynenc_rabbitmq.util.rabbitmq_queue import QueueSpec


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
        }
    )


@pytest.fixture(autouse=True)
def clear_client_instances() -> None:
    """Clear singleton instances before each test."""
    PynencRabbitMqClient._instances.clear()


def test_get_instance_should_create_new_client_when_none_exists(
    rabbitmq_config: ConfigRabbitMq,
) -> None:
    """Test that get_instance creates a new client when no instance exists."""
    # Act
    client = PynencRabbitMqClient.get_instance(rabbitmq_config)

    # Assert
    assert client is not None
    assert client.conf == rabbitmq_config
    assert len(PynencRabbitMqClient._instances) == 1


def test_get_instance_should_return_same_client_when_config_matches(
    rabbitmq_config: ConfigRabbitMq,
) -> None:
    """Test that get_instance returns the same client for matching configuration."""
    # Arrange
    client1 = PynencRabbitMqClient.get_instance(rabbitmq_config)

    # Act
    client2 = PynencRabbitMqClient.get_instance(rabbitmq_config)

    # Assert
    assert client1 is client2
    assert len(PynencRabbitMqClient._instances) == 1


def test_get_instance_should_create_different_clients_when_configs_differ() -> None:
    """Test that different configurations create different client instances."""
    # Arrange
    config1 = ConfigRabbitMq(
        config_values={"rabbitmq_host": "host1", "rabbitmq_port": 5672}
    )
    config2 = ConfigRabbitMq(
        config_values={"rabbitmq_host": "host2", "rabbitmq_port": 5672}
    )

    # Act
    client1 = PynencRabbitMqClient.get_instance(config1)
    client2 = PynencRabbitMqClient.get_instance(config2)

    # Assert
    assert client1 is not client2
    assert len(PynencRabbitMqClient._instances) == 2


def test_get_connection_key_should_build_from_components_when_no_url(
    rabbitmq_config: ConfigRabbitMq,
) -> None:
    """Test that connection key is built from individual components when no URL provided."""
    # Act
    key = PynencRabbitMqClient._get_connection_key(rabbitmq_config)

    # Assert
    assert key == "localhost:5672:/test"


@patch("pynenc_rabbitmq.util.rabbitmq_client.ConnectionManager")
@patch("pynenc_rabbitmq.util.rabbitmq_client.QueueManager")
def test_get_queue_should_create_queue_manager(
    mock_queue_manager: MagicMock,
    mock_connection_manager: MagicMock,
    rabbitmq_config: ConfigRabbitMq,
) -> None:
    """Test that get_queue creates a QueueManager with correct parameters."""
    # Arrange
    client = PynencRabbitMqClient.get_instance(rabbitmq_config)
    spec = QueueSpec(name="test_queue")

    # Act
    _ = client.get_queue("test_queue")

    # Assert
    mock_queue_manager.assert_called_once()
    # Verify the QueueManager was called with connection manager, config, and spec
    call_args = mock_queue_manager.call_args[0]
    assert call_args[1] == spec


@patch("pynenc_rabbitmq.util.rabbitmq_client.ConnectionManager")
def test_close_should_call_connection_manager_close(
    mock_connection_manager_class: MagicMock, rabbitmq_config: ConfigRabbitMq
) -> None:
    """Test that close delegates to the connection manager."""
    # Arrange
    mock_conn_instance = MagicMock()
    mock_connection_manager_class.return_value = mock_conn_instance
    client = PynencRabbitMqClient.get_instance(rabbitmq_config)

    # Act
    client.close()

    # Assert
    mock_conn_instance.close.assert_called_once()
