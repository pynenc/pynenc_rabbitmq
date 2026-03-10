"""
Retry utilities with exponential backoff for RabbitMQ operations.

Provides resilient connection handling by retrying failed operations
with configurable exponential backoff delays.

Key components:
- calculate_backoff_delay: Computes delay for a given retry attempt
- retry_with_backoff: Decorator/wrapper for retryable operations
- RECOVERABLE_EXCEPTIONS: Tuple of exceptions that trigger retry
"""

import logging
import time
from collections.abc import Callable
from typing import TypeVar

import pika.exceptions

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Exceptions that indicate a recoverable connection issue
RECOVERABLE_EXCEPTIONS = (
    pika.exceptions.AMQPConnectionError,
    pika.exceptions.AMQPChannelError,
    pika.exceptions.StreamLostError,
    pika.exceptions.ConnectionClosedByBroker,
    ConnectionError,
    ConnectionResetError,
    BrokenPipeError,
    TimeoutError,
)


def calculate_backoff_delay(
    attempt: int,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
) -> float:
    """
    Calculate exponential backoff delay for a given attempt.

    :param attempt: Current attempt number (0-indexed)
    :param initial_delay: Initial delay in seconds
    :param max_delay: Maximum delay cap in seconds
    :param exponential_base: Base for exponential calculation
    :return: Delay in seconds
    """
    delay = initial_delay * (exponential_base**attempt)
    return min(delay, max_delay)


def retry_with_backoff(
    operation: Callable[[], T],
    operation_name: str,
    max_attempts: int = 0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> T:
    """
    Execute an operation with exponential backoff retry on connection failures.

    :param operation: Callable to execute
    :param operation_name: Name for logging purposes
    :param max_attempts: Maximum retry attempts (0 = infinite)
    :param initial_delay: Initial delay in seconds before first retry
    :param max_delay: Maximum delay between retries
    :param exponential_base: Base for exponential backoff
    :param on_retry: Optional callback called before each retry with (attempt, exception, delay)
    :return: Result of the operation
    :raises: The last exception if max_attempts is reached
    """
    attempt = 0

    while True:
        try:
            return operation()
        except RECOVERABLE_EXCEPTIONS as e:
            attempt += 1

            if max_attempts > 0 and attempt >= max_attempts:
                logger.error(
                    f"Operation '{operation_name}' failed after {attempt} attempts: {e}"
                )
                raise

            delay = calculate_backoff_delay(
                attempt - 1, initial_delay, max_delay, exponential_base
            )

            logger.warning(
                f"RabbitMQ connection error during '{operation_name}' "
                f"(attempt {attempt}{'/' + str(max_attempts) if max_attempts > 0 else ''}): {e}. "
                f"Retrying in {delay:.1f}s..."
            )

            if on_retry:
                on_retry(attempt, e, delay)

            time.sleep(delay)
