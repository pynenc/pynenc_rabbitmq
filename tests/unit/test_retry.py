"""Unit tests for retry utility with exponential backoff."""

from unittest.mock import MagicMock, patch

import pika.exceptions
import pytest

from pynenc_rabbitmq.util.retry import (
    calculate_backoff_delay,
    retry_with_backoff,
)

# Tests for calculate_backoff_delay


def test_calculate_backoff_delay_should_return_initial_delay_on_first_attempt() -> None:
    """First attempt should use initial delay."""
    delay = calculate_backoff_delay(attempt=0, initial_delay=1.0)
    assert delay == 1.0


def test_calculate_backoff_delay_should_grow_exponentially() -> None:
    """Delay should grow exponentially."""
    delays = [calculate_backoff_delay(i, initial_delay=1.0) for i in range(5)]
    assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]


def test_calculate_backoff_delay_should_cap_at_max_delay() -> None:
    """Delay should be capped at max_delay."""
    delay = calculate_backoff_delay(attempt=10, initial_delay=1.0, max_delay=30.0)
    assert delay == 30.0


def test_calculate_backoff_delay_should_use_custom_exponential_base() -> None:
    """Should respect custom exponential base."""
    delay = calculate_backoff_delay(attempt=2, initial_delay=1.0, exponential_base=3.0)
    assert delay == 9.0  # 1.0 * 3^2


# Tests for retry_with_backoff


def test_retry_with_backoff_should_return_result_on_first_success() -> None:
    """Should return result immediately on success."""
    operation = MagicMock(return_value="success")

    result = retry_with_backoff(operation, "test_op")

    assert result == "success"
    assert operation.call_count == 1


def test_retry_with_backoff_should_retry_on_connection_error() -> None:
    """Should retry on AMQPConnectionError."""
    operation = MagicMock(
        side_effect=[pika.exceptions.AMQPConnectionError(), "success"]
    )

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        result = retry_with_backoff(operation, "test_op", initial_delay=0.1)

    assert result == "success"
    assert operation.call_count == 2


def test_retry_with_backoff_should_retry_on_stream_lost_error() -> None:
    """Should retry on StreamLostError."""
    operation = MagicMock(
        side_effect=[pika.exceptions.StreamLostError("lost"), "success"]
    )

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        result = retry_with_backoff(operation, "test_op", initial_delay=0.1)

    assert result == "success"
    assert operation.call_count == 2


def test_retry_with_backoff_should_raise_after_max_attempts() -> None:
    """Should raise after max_attempts."""
    operation = MagicMock(side_effect=pika.exceptions.AMQPConnectionError())

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        with pytest.raises(pika.exceptions.AMQPConnectionError):
            retry_with_backoff(operation, "test_op", max_attempts=3, initial_delay=0.1)

    assert operation.call_count == 3


def test_retry_with_backoff_should_retry_indefinitely_when_max_attempts_zero() -> None:
    """Should keep retrying when max_attempts is 0 (infinite)."""
    operation = MagicMock(
        side_effect=[
            pika.exceptions.AMQPConnectionError(),
            pika.exceptions.AMQPConnectionError(),
            pika.exceptions.AMQPConnectionError(),
            pika.exceptions.AMQPConnectionError(),
            pika.exceptions.AMQPConnectionError(),
            "success",
        ]
    )

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        result = retry_with_backoff(
            operation, "test_op", max_attempts=0, initial_delay=0.1
        )

    assert result == "success"
    assert operation.call_count == 6


def test_retry_with_backoff_should_call_on_retry_callback() -> None:
    """Should call on_retry callback before each retry."""
    operation = MagicMock(
        side_effect=[
            pika.exceptions.AMQPConnectionError(),
            pika.exceptions.AMQPConnectionError(),
            "success",
        ]
    )
    on_retry = MagicMock()

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        retry_with_backoff(
            operation,
            "test_op",
            initial_delay=1.0,
            on_retry=on_retry,
        )

    assert on_retry.call_count == 2
    # First retry: attempt=1, delay=1.0
    assert on_retry.call_args_list[0][0][0] == 1
    assert on_retry.call_args_list[0][0][2] == 1.0
    # Second retry: attempt=2, delay=2.0
    assert on_retry.call_args_list[1][0][0] == 2
    assert on_retry.call_args_list[1][0][2] == 2.0


def test_retry_with_backoff_should_not_retry_non_recoverable_exceptions() -> None:
    """Should not retry on non-recoverable exceptions."""
    operation = MagicMock(side_effect=ValueError("not recoverable"))

    with pytest.raises(ValueError, match="not recoverable"):
        retry_with_backoff(operation, "test_op")

    assert operation.call_count == 1


def test_retry_with_backoff_should_use_exponential_backoff_sleep() -> None:
    """Should sleep with exponential backoff delays."""
    operation = MagicMock(
        side_effect=[
            pika.exceptions.AMQPConnectionError(),
            pika.exceptions.AMQPConnectionError(),
            pika.exceptions.AMQPConnectionError(),
            "success",
        ]
    )

    with patch("pynenc_rabbitmq.util.retry.time.sleep") as mock_sleep:
        retry_with_backoff(
            operation,
            "test_op",
            initial_delay=1.0,
            exponential_base=2.0,
        )

    assert mock_sleep.call_count == 3
    assert mock_sleep.call_args_list[0][0][0] == 1.0
    assert mock_sleep.call_args_list[1][0][0] == 2.0
    assert mock_sleep.call_args_list[2][0][0] == 4.0


@pytest.mark.parametrize(
    "exception_class",
    [
        pika.exceptions.AMQPConnectionError,
        pika.exceptions.StreamLostError,
        ConnectionError,
        ConnectionResetError,
        BrokenPipeError,
        TimeoutError,
    ],
)
def test_retry_with_backoff_should_retry_all_recoverable_exceptions(
    exception_class: type[Exception],
) -> None:
    """Should retry on all defined recoverable exceptions."""
    if exception_class == pika.exceptions.StreamLostError:
        exc = exception_class("error")
    else:
        exc = exception_class()

    operation = MagicMock(side_effect=[exc, "success"])

    with patch("pynenc_rabbitmq.util.retry.time.sleep"):
        result = retry_with_backoff(operation, "test_op", initial_delay=0.1)

    assert result == "success"
    assert operation.call_count == 2
