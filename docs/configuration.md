# Configuration Reference

All settings can be provided via the builder, environment variables, or YAML config files.
See the [Pynenc configuration guide](https://pynenc.readthedocs.io/en/latest/configuration/index.html) for the general mechanism.

## Connection Settings — `ConfigRabbitMq`

| Setting                        | Type    | Default       | Description                                        |
| ------------------------------ | ------- | ------------- | -------------------------------------------------- |
| `rabbitmq_host`                | `str`   | `"localhost"` | RabbitMQ server hostname                           |
| `rabbitmq_port`                | `int`   | `5672`        | AMQP port                                          |
| `rabbitmq_username`            | `str`   | `"guest"`     | Authentication username                            |
| `rabbitmq_password`            | `str`   | `"guest"`     | Authentication password                            |
| `rabbitmq_virtual_host`        | `str`   | `"/"`         | Virtual host partition                             |
| `rabbitmq_connection_attempts` | `int`   | `3`           | Maximum connection retry attempts                  |
| `rabbitmq_retry_delay`         | `float` | `5.0`         | Delay between connection retries (seconds)         |
| `rabbitmq_heartbeat`           | `int`   | `600`         | AMQP heartbeat interval in seconds; `0` to disable |

## Queue & Exchange Settings

| Setting                  | Type  | Default           | Description                                   |
| ------------------------ | ----- | ----------------- | --------------------------------------------- |
| `rabbitmq_queue_prefix`  | `str` | `"pynenc"`        | Prefix for all queue names                    |
| `rabbitmq_exchange_name` | `str` | `"pynenc.direct"` | Exchange name for message routing             |
| `rabbitmq_exchange_type` | `str` | `"direct"`        | Exchange type: `direct`, `topic`, or `fanout` |

## Consumer & Delivery Settings

| Setting                     | Type   | Default    | Description                                     |
| --------------------------- | ------ | ---------- | ----------------------------------------------- |
| `rabbitmq_prefetch_count`   | `int`  | `10`       | Max unacknowledged messages per consumer        |
| `rabbitmq_message_ttl`      | `int`  | `86400000` | Message TTL in milliseconds (default: 24 hours) |
| `rabbitmq_confirm_delivery` | `bool` | `True`     | Enable publisher confirms for reliable delivery |

## Retry Settings

| Setting                           | Type    | Default | Description                                   |
| --------------------------------- | ------- | ------- | --------------------------------------------- |
| `rabbitmq_retry_max_attempts`     | `int`   | `0`     | Max operation retry attempts (`0` = infinite) |
| `rabbitmq_retry_initial_delay`    | `float` | `1.0`   | Initial retry delay (seconds)                 |
| `rabbitmq_retry_max_delay`        | `float` | `60.0`  | Maximum retry delay (seconds)                 |
| `rabbitmq_retry_exponential_base` | `float` | `2.0`   | Exponential backoff multiplier                |

## Logging Settings

| Setting                   | Type  | Default     | Description                                                         |
| ------------------------- | ----- | ----------- | ------------------------------------------------------------------- |
| `rabbitmq_pika_log_level` | `str` | `"WARNING"` | Log level for the pika library: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Environment Variables

Every setting maps to `PYNENC_{SETTING_UPPERCASE}`:

```bash
export PYNENC_RABBITMQ_HOST="rabbitmq.example.com"
export PYNENC_RABBITMQ_PASSWORD="mysecret"
export PYNENC_RABBITMQ_PREFETCH_COUNT=5
export PYNENC_RABBITMQ_PIKA_LOG_LEVEL=INFO
```

## YAML Configuration

```yaml
# pynenc.yaml
rabbitmq_host: "rabbitmq.example.com"
rabbitmq_virtual_host: "/staging"
rabbitmq_prefetch_count: 5
rabbitmq_retry_max_attempts: 10
rabbitmq_pika_log_level: "INFO"
```
