"""Queue manager for RabbitMQ operations with automatic retry."""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pika

from pynenc_rabbitmq.util.retry import RECOVERABLE_EXCEPTIONS, retry_with_backoff

if TYPE_CHECKING:
    from pynenc_rabbitmq.util.rabbitmq_conn_mng import ConnectionManager
    from pynenc_rabbitmq.util.rabbitmq_queue import QueueSpec

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages queue operations with automatic retry on connection failures.

    Wraps all queue operations with exponential backoff retry logic
    to handle transient connection issues gracefully.
    """

    def __init__(
        self, connection_manager: "ConnectionManager", spec: "QueueSpec"
    ) -> None:
        self._connection_manager = connection_manager
        self._spec = spec

    def _get_retry_config(self) -> dict[str, Any]:
        """Get retry configuration from connection manager config."""
        conf = self._connection_manager.conf
        return {
            "max_attempts": conf.rabbitmq_retry_max_attempts,
            "initial_delay": conf.rabbitmq_retry_initial_delay,
            "max_delay": conf.rabbitmq_retry_max_delay,
            "exponential_base": conf.rabbitmq_retry_exponential_base,
        }

    def _retry_operation(
        self, operation: Callable[[], Any], operation_name: str
    ) -> Any:
        """Execute operation with configured retry logic."""
        retry_config = self._get_retry_config()
        return retry_with_backoff(
            operation=operation,
            operation_name=f"{operation_name}[{self._spec.name}]",
            **retry_config,
        )

    def publish_message(self, message: str) -> bool:
        """
        Publish a message to the queue with retry logic.

        :param message: Message content to publish
        :return: True if successful, False on error
        """

        def _publish() -> bool:
            try:
                with self._connection_manager.get_channel() as channel:
                    channel.queue_declare(
                        queue=self._spec.name, durable=self._spec.durable
                    )
                    properties = pika.BasicProperties(
                        delivery_mode=2 if self._spec.durable else 1
                    )
                    channel.basic_publish(
                        exchange=self._spec.exchange,
                        routing_key=self._spec.routing_key,
                        body=message.encode(),
                        properties=properties,
                    )
                    return True
            except RECOVERABLE_EXCEPTIONS:
                # Re-raise recoverable exceptions for retry logic
                raise
            except Exception as e:
                logger.error(
                    f"Failed to publish message to queue {self._spec.name}: {e}",
                    exc_info=True,
                )
                return False

        return self._retry_operation(_publish, "publish_message")

    def consume_message(self) -> str | None:
        """
        Consume a single message from the queue with retry logic.

        :return: Message content or None if queue is empty
        """

        def _consume() -> str | None:
            try:
                with self._connection_manager.get_channel() as channel:
                    channel.queue_declare(
                        queue=self._spec.name, durable=self._spec.durable
                    )
                    method, _, body = channel.basic_get(
                        queue=self._spec.name, auto_ack=True
                    )
                    if method:
                        return body.decode()
                    return None
            except RECOVERABLE_EXCEPTIONS:
                raise
            except Exception as e:
                logger.error(
                    f"Failed to consume message from queue {self._spec.name}: {e}",
                    exc_info=True,
                )
                return None

        return self._retry_operation(_consume, "consume_message")

    def get_message_count(self) -> int:
        """
        Get the number of messages in the queue with retry logic.

        :return: Number of messages in queue
        """

        def _count() -> int:
            with self._connection_manager.get_channel() as channel:
                result = channel.queue_declare(
                    queue=self._spec.name, durable=self._spec.durable, passive=True
                )
                return result.method.message_count

        return self._retry_operation(_count, "get_message_count")

    def purge_queue(self) -> int:
        """
        Clear all messages from the queue with retry logic.

        :return: Number of messages purged
        """

        def _purge() -> int:
            with self._connection_manager.get_channel() as channel:
                channel.queue_declare(queue=self._spec.name, durable=self._spec.durable)
                result = channel.queue_purge(queue=self._spec.name)
                return result.method.message_count

        return self._retry_operation(_purge, "purge_queue")
