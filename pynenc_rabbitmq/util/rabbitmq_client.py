"""Simple RabbitMQ client for Pynenc."""

import logging
import threading
from typing import TYPE_CHECKING

from pynenc_rabbitmq.util.rabbitmq_conn_mng import ConnectionManager
from pynenc_rabbitmq.util.rabbitmq_queue import QueueSpec
from pynenc_rabbitmq.util.rabbitmq_queue_mng import QueueManager

if TYPE_CHECKING:
    from pynenc_rabbitmq.conf.config_rabbitmq import ConfigRabbitMq


class PynencRabbitMqClient:
    """
    RabbitMQ client for sending and receiving strings.

    Thread-safe singleton per configuration. Uses thread-local connections internally.
    """

    _instances: dict[str, "PynencRabbitMqClient"] = {}
    _lock = threading.RLock()

    def __init__(self, conf: "ConfigRabbitMq") -> None:
        self.conf = conf
        # Configure pika logging level to reduce noise
        self._configure_pika_logging()
        # ConnectionManager handles thread-local connections internally
        self._connection_manager = ConnectionManager(conf)

    def _configure_pika_logging(self) -> None:
        """Configure pika library logging level based on configuration."""
        pika_logger = logging.getLogger("pika")
        log_level = getattr(
            logging, self.conf.rabbitmq_pika_log_level.upper(), logging.WARNING
        )
        pika_logger.setLevel(log_level)

    @classmethod
    def get_instance(cls, conf: "ConfigRabbitMq") -> "PynencRabbitMqClient":
        """
        Get or create a singleton instance for the given configuration.

        One instance per configuration, but each thread gets its own connection.

        :param conf: RabbitMQ configuration
        :return: Singleton client instance for this configuration
        """
        key = cls._get_connection_key(conf)
        with cls._lock:
            if key not in cls._instances:
                cls._instances[key] = cls(conf)
            return cls._instances[key]

    @staticmethod
    def _get_connection_key(conf: "ConfigRabbitMq") -> str:
        """Generate a unique connection key based on configuration."""
        return f"{conf.rabbitmq_host}:{conf.rabbitmq_port}:{conf.rabbitmq_virtual_host}"

    def get_queue(self, queue_name: str) -> QueueManager:
        """
        Get a queue manager for the specified queue.

        :param queue_name: Name of the queue
        :return: Queue manager instance
        """
        spec = QueueSpec(name=queue_name, durable=True)
        return QueueManager(self._connection_manager, spec)

    def close(self) -> None:
        """Close the thread-local connection for current thread."""
        self._connection_manager.close()
