# Installation & Quick Start

## Install

```bash
pip install pynenc-rabbitmq
```

The plugin registers itself automatically via the `pynenc.plugins` entry point — no extra configuration needed.

## Quick Start

RabbitMQ only provides a broker, so combine it with another backend for orchestration and state:

### With Redis for State

```python
from pynenc import PynencBuilder

app = (
    PynencBuilder()
    .app_id("my_app")
    .redis(url="redis://localhost:6379")     # state, orchestrator, etc.
    .rabbitmq_broker(host="localhost")        # swap broker to RabbitMQ
    .process_runner()
    .build()
)

@app.task
def add(x: int, y: int) -> int:
    return x + y

result = add(1, 2).result  # 3
```

### With MongoDB for State

```python
app = (
    PynencBuilder()
    .app_id("my_app")
    .mongo(url="mongodb://localhost:27017/pynenc")
    .rabbitmq_broker(host="rabbitmq.example.com")
    .process_runner()
    .build()
)
```

### Docker Compose

```yaml
services:
  redis:
    image: redis:7

  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]

  worker:
    build: .
    environment:
      PYNENC_REDIS_URL: redis://redis:6379
      PYNENC_RABBITMQ_HOST: rabbitmq
    depends_on: [redis, rabbitmq]
    command: pynenc worker
```

## Builder Methods

### `.rabbitmq_broker(host, port, username, password, virtual_host, queue_prefix, exchange_name, exchange_type)`

Configure RabbitMQ as the message broker.

```python
builder.rabbitmq_broker(
    host="rabbitmq.example.com",
    port=5672,
    username="guest",
    password="guest",
    virtual_host="/",
)
```

| Parameter       | Type          | Description                                   |
| --------------- | ------------- | --------------------------------------------- |
| `host`          | `str \| None` | RabbitMQ hostname                             |
| `port`          | `int \| None` | AMQP port                                     |
| `username`      | `str \| None` | Authentication username                       |
| `password`      | `str \| None` | Authentication password                       |
| `virtual_host`  | `str \| None` | RabbitMQ virtual host                         |
| `queue_prefix`  | `str \| None` | Prefix for all queue names                    |
| `exchange_name` | `str \| None` | Exchange name for message routing             |
| `exchange_type` | `str \| None` | Exchange type: `direct`, `topic`, or `fanout` |
