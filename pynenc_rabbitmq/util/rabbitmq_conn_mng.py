"""RabbitMQ connection management with thread safety."""

import logging
import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pika

if TYPE_CHECKING:
    from collections.abc import Generator

    from pynenc_rabbitmq.conf.config_rabbitmq import ConfigRabbitMq

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages RabbitMQ connections with thread safety using thread-local storage."""

    def __init__(self, conf: "ConfigRabbitMq") -> None:
        self.conf = conf
        self._local = threading.local()
        self._lock = threading.RLock()

    def _get_connection_parameters(self) -> pika.ConnectionParameters:
        """
        Create connection parameters from configuration.

        :return: Configured connection parameters for RabbitMQ
        """
        credentials = pika.PlainCredentials(
            self.conf.rabbitmq_username, self.conf.rabbitmq_password
        )

        return pika.ConnectionParameters(
            host=self.conf.rabbitmq_host,
            port=self.conf.rabbitmq_port,
            virtual_host=self.conf.rabbitmq_virtual_host,
            credentials=credentials,
            heartbeat=self.conf.rabbitmq_heartbeat,
            connection_attempts=self.conf.rabbitmq_connection_attempts,
            retry_delay=self.conf.rabbitmq_retry_delay,
        )

    def _ensure_connection(self) -> pika.BlockingConnection:
        """
        Ensure we have a valid thread-local connection.

        Creates one connection per thread since BlockingConnection is not thread-safe.

        :return: Active BlockingConnection instance for current thread
        """
        # Check if current thread has a connection
        if (
            not hasattr(self._local, "connection")
            or self._local.connection is None
            or self._local.connection.is_closed
        ):
            with self._lock:
                # Double-check after acquiring lock
                if (
                    not hasattr(self._local, "connection")
                    or self._local.connection is None
                    or self._local.connection.is_closed
                ):
                    logger.info(
                        "Creating new RabbitMQ connection for thread %s to %s:%s/%s",
                        threading.current_thread().name,
                        self.conf.rabbitmq_host,
                        self.conf.rabbitmq_port,
                        self.conf.rabbitmq_virtual_host,
                    )
                    params = self._get_connection_parameters()
                    self._local.connection = pika.BlockingConnection(params)
                    logger.info(
                        "RabbitMQ connection established for thread %s",
                        threading.current_thread().name,
                    )
        return self._local.connection

    @contextmanager
    def get_channel(
        self,
    ) -> "Generator[pika.adapters.blocking_connection.BlockingChannel, None, None]":
        """
        Get a channel within a context manager for safe cleanup.

        Each thread gets its own connection, and channels are created per operation.

        :return: Generator yielding an open channel
        """
        connection = self._ensure_connection()
        channel = connection.channel()

        if self.conf.rabbitmq_confirm_delivery:
            channel.confirm_delivery()

        channel.basic_qos(prefetch_count=self.conf.rabbitmq_prefetch_count)

        try:
            yield channel
        finally:
            try:
                if channel.is_open:
                    channel.close()
            except Exception as e:
                logger.debug("Error closing channel (may already be closed): %s", e)

    def close(self) -> None:
        """Close the thread-local connection if open."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            try:
                if not self._local.connection.is_closed:
                    self._local.connection.close()
                    logger.info(
                        "RabbitMQ connection closed for thread %s",
                        threading.current_thread().name,
                    )
            except Exception as e:
                logger.debug("Error closing connection (may already be closed): %s", e)
            finally:
                self._local.connection = None
