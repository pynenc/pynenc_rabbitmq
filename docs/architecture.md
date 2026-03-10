# Architecture

How `pynenc-rabbitmq` uses RabbitMQ internally.

## Thread-Safe Connections

RabbitMQ's `BlockingConnection` is not thread-safe. The plugin uses `threading.local()`
to maintain **one connection per thread**. A `ConnectionManager` handles lifecycle —
creation, health checks, and cleanup. Channels are obtained via a context manager that
ensures proper release even on errors.

## Message Persistence

All queues are created as **durable** (survive broker restarts) and messages use
**delivery mode 2** (persistent on disk). Combined with publisher confirms (enabled by
default via `rabbitmq_confirm_delivery`), messages are not lost even if the RabbitMQ
server restarts mid-operation.

## Automatic Retries

All queue operations — publish, consume, count, purge — are wrapped with exponential
backoff. Recoverable exceptions include:

- `AMQPConnectionError`, `StreamLostError`, `ConnectionClosedByBroker`
- `ConnectionResetError`, `BrokenPipeError`, `TimeoutError`

By default retries are **infinite** (`rabbitmq_retry_max_attempts=0`) with delays
growing from 1 s up to 60 s. Set a positive value to limit retries.

## Queue Naming

The broker message queue is named:

```
{queue_prefix}_broker_messages
```

Default: `pynenc_broker_messages`. The queue prefix can be changed per-environment
to isolate staging and production queues on a shared broker.

## Logging

The plugin uses multiple loggers at different levels:

| Logger / Area          | Level        | What's logged                                         |
| ---------------------- | ------------ | ----------------------------------------------------- |
| **Connection Manager** | `INFO`       | Connection lifecycle: creation, established, closed   |
| **Retry Module**       | `WARNING`    | Retry attempts with delay info                        |
| **Retry Module**       | `ERROR`      | Final failures after all retries exhausted            |
| **Queue Manager**      | `ERROR`      | Operation failures with full exception info           |
| **Pika library**       | configurable | Set via `rabbitmq_pika_log_level` (default `WARNING`) |

```{tip}
Set `rabbitmq_pika_log_level: INFO` in your config to see connection establishment
details, or `DEBUG` for full AMQP frame-level tracing during development.
```
