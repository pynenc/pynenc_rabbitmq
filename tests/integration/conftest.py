"""
Integration test configuration with real RabbitMQ using testcontainers.

This conftest provides fixtures for integration testing with a real RabbitMQ instance
running in a Docker container.
"""

import os
import tempfile
from typing import TYPE_CHECKING

import pytest
from docker.errors import DockerException
from pynenc import PynencBuilder
from pynenc_tests.util.log import create_test_logger
from testcontainers.rabbitmq import RabbitMqContainer

from pynenc_rabbitmq.util.rabbitmq_client import PynencRabbitMqClient

if TYPE_CHECKING:
    from collections.abc import Generator

    from pynenc import Pynenc

logger = create_test_logger(__name__)


@pytest.fixture(scope="session")
def rabbitmq_container() -> "Generator[RabbitMqContainer, None, None]":
    """
    Start a RabbitMQ container for integration testing.

    Uses testcontainers to spin up a real RabbitMQ instance in Docker.
    The container is shared across the test session for performance.

    :return: Generator yielding a running RabbitMQ container
    :raises RuntimeError: If Docker is not running or accessible
    """
    try:
        container = RabbitMqContainer("rabbitmq:3.13-management")
        container.start()

        # Debug: logger.info connection details
        host = container.get_container_host_ip()
        port = container.get_exposed_port(container.port)
        logger.info(f"\n{'=' * 80}")
        logger.info("RabbitMQ Container Started:")
        logger.info(f"  Host: {host}")
        logger.info(f"  Port (exposed): {port}")
        logger.info(f"  Port (internal): {container.port}")
        logger.info(f"  Username: {container.username}")
        logger.info(f"  Virtual Host: {container.vhost}")
        logger.info(f"{'=' * 80}\n")

        # Try to get container logs
        try:
            logs = container.get_logs()
            logger.info(f"\n{'=' * 80}\nRabbitMQ Container Logs:\n{'=' * 80}")
            if isinstance(logs, tuple) and len(logs) > 0:
                stdout_logs = (
                    logs[0].decode("utf-8")
                    if isinstance(logs[0], bytes)
                    else str(logs[0])
                )
                # logger.info last 50 lines to avoid overwhelming output
                logger.info("\n".join(stdout_logs.split("\n")[-50:]))
            else:
                logger.info(f"Logs format: {type(logs)}")
                logger.info(str(logs))
            logger.info("=" * 80 + "\n")
        except Exception as e:
            logger.info(f"Could not fetch container logs: {e}")

        yield container

        container.stop()
    except DockerException as e:
        raise RuntimeError(
            "Docker is not running or not accessible. "
            "Please start Docker to run integration tests."
        ) from e


@pytest.fixture(scope="function")
def temp_sqlite_db_path() -> "Generator[str, None, None]":
    """
    Create a temporary SQLite database for testing.

    :return: Generator yielding path to temporary database file
    """
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    logger.info(f"\n[TEST] Created temporary SQLite DB at: {path}")

    yield path

    # Cleanup
    try:
        os.unlink(path)
        logger.info(f"\n[TEST] Removed temporary SQLite DB at: {path}")
    except Exception as e:
        logger.info(f"\n[TEST] Could not remove temp DB {path}: {e}")


@pytest.fixture(scope="function")
def app_instance_builder(
    rabbitmq_container: RabbitMqContainer, temp_sqlite_db_path: str
) -> "Generator['PynencBuilder', None, None]":
    """
    Provide a PynencBuilder configured with RabbitMQ for integration tests.

    :param rabbitmq_container: Running RabbitMQ container
    :param temp_sqlite_db_path: Path to temporary SQLite database
    :return: Generator yielding a configured PynencBuilder instance
    """
    # Clear singleton instances before creating new app
    PynencRabbitMqClient._instances.clear()

    # Get connection details from container
    host = rabbitmq_container.get_container_host_ip()
    port = int(rabbitmq_container.get_exposed_port(rabbitmq_container.port))

    logger.info(f"\nConfiguring app with RabbitMQ: {host}:{port}")

    # Use .rabbitmq_broker() method (not .rabbitmq())
    builder = (
        PynencBuilder()
        .sqlite(temp_sqlite_db_path)
        .rabbitmq_broker(
            host=host,
            port=port,
            username=rabbitmq_container.username,
            password=rabbitmq_container.password,
            virtual_host=rabbitmq_container.vhost,
        )
    )

    yield builder

    # Cleanup
    PynencRabbitMqClient._instances.clear()


@pytest.fixture(scope="function")
def app_instance(
    app_instance_builder: "PynencBuilder",
) -> "Generator['Pynenc', None, None]":
    """
    Provide a Pynenc app instance with real RabbitMQ backend for integration tests.

    :param app_instance_builder: Configured PynencBuilder instance
    :return: Generator yielding a Pynenc app instance
    """
    app = app_instance_builder.build()

    yield app

    # Cleanup
    app.purge()
