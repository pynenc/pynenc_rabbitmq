"""Simple RabbitMQ queue operations for sending and receiving strings."""

import logging
from typing import TYPE_CHECKING

import pika

if TYPE_CHECKING:
    from pynenc_rabbitmq.util.rabbitmq_conn_mng import ConnectionManager
    from pynenc_rabbitmq.util.rabbitmq_queue import QueueSpec

logger = logging.getLogger(__name__)


class QueueManager:
    """Manages simple string message operations on a RabbitMQ queue."""

    def __init__(
        self,
        connection_manager: "ConnectionManager",
        spec: "QueueSpec",
    ) -> None:
        self._connection_manager = connection_manager
        self._spec = spec

    def publish_message(self, message: str) -> bool:
        """
        Publish a string message to the queue.

        :param message: String message to publish
        :return: True if message was published successfully
        """
        try:
            with self._connection_manager.get_channel() as channel:
                # Declare queue
                channel.queue_declare(
                    queue=self._spec.name,
                    durable=self._spec.durable,
                    exclusive=self._spec.exclusive,
                    auto_delete=self._spec.auto_delete,
                    arguments=self._spec.arguments,
                )

                channel.basic_publish(
                    exchange=self._spec.exchange,
                    routing_key=self._spec.routing_key,
                    body=message.encode(),
                    properties=pika.BasicProperties(
                        delivery_mode=2 if self._spec.durable else 1,
                    ),
                )
                logger.debug("Published message to queue %s", self._spec.name)
                return True
        except Exception as e:
            logger.error(
                "Failed to publish message to queue %s: %s",
                self._spec.name,
                e,
                exc_info=True,
            )
            return False

    def consume_message(self) -> str | None:
        """
        Consume a single string message from the queue.

        :return: Message string if available, None otherwise
        """
        try:
            with self._connection_manager.get_channel() as channel:
                # Declare queue
                channel.queue_declare(
                    queue=self._spec.name,
                    durable=self._spec.durable,
                    exclusive=self._spec.exclusive,
                    auto_delete=self._spec.auto_delete,
                    arguments=self._spec.arguments,
                )

                # Get single message
                method_frame, _header_frame, body = channel.basic_get(
                    queue=self._spec.name, auto_ack=True
                )

                if method_frame and body:
                    return body.decode()
                return None
        except Exception as e:
            logger.error(
                "Failed to consume message from queue %s: %s",
                self._spec.name,
                e,
                exc_info=True,
            )
            return None

    def get_message_count(self) -> int:
        """
        Get the number of messages in the queue.

        :return: Number of messages in queue
        """
        try:
            with self._connection_manager.get_channel() as channel:
                result = channel.queue_declare(
                    queue=self._spec.name,
                    durable=self._spec.durable,
                    exclusive=self._spec.exclusive,
                    auto_delete=self._spec.auto_delete,
                    arguments=self._spec.arguments,
                    passive=True,
                )
                return result.method.message_count
        except Exception as e:
            logger.debug(
                "Failed to get message count for queue %s: %s", self._spec.name, e
            )
            return 0

    def purge_queue(self) -> int:
        """
        Remove all messages from the queue.

        :return: Number of messages purged
        """
        try:
            with self._connection_manager.get_channel() as channel:
                result = channel.queue_purge(queue=self._spec.name)
                return result.method.message_count
        except Exception as e:
            logger.error(
                "Failed to purge queue %s: %s", self._spec.name, e, exc_info=True
            )
            return 0
