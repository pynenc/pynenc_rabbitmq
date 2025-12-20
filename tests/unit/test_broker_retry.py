"""Unit tests verifying broker uses queue manager with retry."""

from unittest.mock import MagicMock, patch


def test_broker_should_delegate_to_queue_manager() -> None:
    """Broker should delegate operations to queue manager which handles retry."""
    with patch(
        "pynenc_rabbitmq.broker.rabbitmq_broker.PynencRabbitMqClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_queue = MagicMock()
        mock_queue.publish_message.return_value = True
        mock_queue.consume_message.return_value = "invocation-id"
        mock_queue.get_message_count.return_value = 42
        mock_client.get_queue.return_value = mock_queue
        mock_client_class.get_instance.return_value = mock_client

        mock_app = MagicMock()
        mock_app.config_values = {}
        mock_app.config_filepath = None
        mock_app.logger = MagicMock()

        from pynenc_rabbitmq.broker.rabbitmq_broker import RabbitMqBroker

        broker = RabbitMqBroker(mock_app)

        # Test send_message delegates to queue manager
        broker.send_message("test-id")
        mock_queue.publish_message.assert_called_once_with("test-id")

        # Test retrieve_invocation delegates to queue manager
        result = broker.retrieve_invocation()
        assert result == "invocation-id"
        mock_queue.consume_message.assert_called_once()

        # Test count_invocations delegates to queue manager
        count = broker.count_invocations()
        assert count == 42
        mock_queue.get_message_count.assert_called_once()

        # Test purge delegates to queue manager
        broker.purge()
        mock_queue.purge_queue.assert_called_once()
