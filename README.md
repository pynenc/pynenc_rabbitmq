<p align="center">
  <img src="https://pynenc.org/assets/img/pynenc_logo.png" alt="Pynenc" width="300">
</p>
<h1 align="center">Pynenc RabbitMQ Plugin</h1>
<p align="center">
    <em>RabbitMQ broker for Pynenc distributed task orchestration</em>
</p>
<p align="center">
    <a href="https://pypi.org/project/pynenc-rabbitmq" target="_blank">
        <img src="https://img.shields.io/pypi/v/pynenc-rabbitmq?color=%2334D058&label=pypi%20package" alt="Package version">
    </a>
    <a href="https://pypi.org/project/pynenc-rabbitmq" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/pynenc-rabbitmq.svg?color=%2334D058" alt="Supported Python versions">
    </a>
    <a href="https://github.com/pynenc/pynenc-rabbitmq/commits/main">
        <img src="https://img.shields.io/github/last-commit/pynenc/pynenc-rabbitmq" alt="GitHub last commit">
    </a>
    <a href="https://github.com/pynenc/pynenc-rabbitmq/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/pynenc/pynenc-rabbitmq" alt="GitHub license">
    </a>
</p>

---

**Documentation**: <a href="https://pynenc-rabbitmq.readthedocs.io" target="_blank">https://pynenc-rabbitmq.readthedocs.io</a>

**Pynenc Documentation**: <a href="https://docs.pynenc.org" target="_blank">https://docs.pynenc.org</a>

**Source Code**: <a href="https://github.com/pynenc/pynenc-rabbitmq" target="_blank">https://github.com/pynenc/pynenc-rabbitmq</a>

---

The `pynenc-rabbitmq` plugin adds a durable RabbitMQ message broker to [Pynenc](https://github.com/pynenc/pynenc). Since RabbitMQ only covers brokering, pair it with the [Redis](https://github.com/pynenc/pynenc-redis) or [MongoDB](https://github.com/pynenc/pynenc-mongodb) plugin for the full Pynenc stack (orchestrator, state backend, triggers, client data store).

## Component

| Component  | Class            | Role                                                                |
| ---------- | ---------------- | ------------------------------------------------------------------- |
| **Broker** | `RabbitMqBroker` | Persistent FIFO queue with publisher confirms and automatic retries |

## Installation

```bash
pip install pynenc-rabbitmq
```

The plugin registers itself automatically via Python entry points when installed.

## Quick Start

RabbitMQ handles brokering — pair it with Redis or MongoDB for the remaining components:

```python
from pynenc import PynencBuilder

# RabbitMQ broker + Redis for state, orchestrator, triggers
app = (
    PynencBuilder()
    .app_id("my_app")
    .redis(url="redis://localhost:6379")       # state, orchestrator, trigger
    .rabbitmq_broker(host="localhost")          # swap broker to RabbitMQ
    .process_runner()
    .build()
)

@app.task
def add(x: int, y: int) -> int:
    return x + y

result = add(1, 2).result  # 3
```

### With MongoDB Instead

```python
app = (
    PynencBuilder()
    .app_id("my_app")
    .mongo(url="mongodb://localhost:27017/pynenc")  # state, orchestrator, trigger
    .rabbitmq_broker(host="localhost")               # swap broker to RabbitMQ
    .process_runner()
    .build()
)
```

## Configuration

### Builder Parameters

```python
app = (
    PynencBuilder()
    .app_id("my_app")
    .redis(url="redis://localhost:6379")
    .rabbitmq_broker(
        host="localhost",
        port=5672,
        username="guest",
        password="guest",
        virtual_host="/",
        queue_prefix="pynenc",
        exchange_name="pynenc",
        exchange_type="direct",
    )
    .build()
)
```

### Environment Variables

```bash
PYNENC__RABBITMQ__HOST="localhost"
PYNENC__RABBITMQ__PORT=5672
PYNENC__RABBITMQ__USERNAME="guest"
PYNENC__RABBITMQ__PASSWORD="guest"
PYNENC__RABBITMQ__VIRTUAL_HOST="/"
```

## Requirements

- Python >= 3.11
- Pynenc >= 0.1.0
- pika >= 1.3.2
- A running RabbitMQ server
- A Redis or MongoDB plugin for the remaining Pynenc components

## Related Plugins

- **[pynenc-redis](https://github.com/pynenc/pynenc-redis)**: Full-stack Redis backend (orchestrator, broker, state, triggers, client data store)
- **[pynenc-mongodb](https://github.com/pynenc/pynenc-mongodb)**: Full-stack MongoDB backend

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
