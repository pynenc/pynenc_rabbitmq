:::{image} \_static/logo.png
:alt: Pynenc
:align: center
:height: 90px
:class: hero-logo
:::

# Pynenc RabbitMQ Plugin

**RabbitMQ broker for [Pynenc](https://pynenc.readthedocs.io/) distributed task orchestration.**

The `pynenc-rabbitmq` plugin adds a durable, persistent RabbitMQ message broker to
Pynenc. Since RabbitMQ only covers brokering, pair it with the Redis or MongoDB plugin
for the full Pynenc stack.

```bash
pip install pynenc-rabbitmq
```

## Component

| Component  | Class            | Role                                                                |
| ---------- | ---------------- | ------------------------------------------------------------------- |
| **Broker** | `RabbitMqBroker` | Persistent FIFO queue with publisher confirms and automatic retries |

---

## Quick Start

RabbitMQ only covers brokering — pair it with Redis or MongoDB for the rest:

```python
from pynenc import PynencBuilder

app = (
    PynencBuilder()
    .app_id("my_app")
    .redis(url="redis://localhost:6379")      # state, orchestrator, trigger
    .rabbitmq_broker(host="localhost")         # swap broker to RabbitMQ
    .process_runner()
    .build()
)

@app.task
def add(x: int, y: int) -> int:
    return x + y
```

See {doc}`installation` for a MongoDB variant and Docker Compose examples.

---

::::{grid} 1 2 3 3
:gutter: 3
:padding: 0

:::{grid-item-card} 🚀 Installation & Quick Start
:link: installation
:link-type: doc
:shadow: sm

Combine RabbitMQ with Redis or MongoDB state backends. Includes PynencBuilder examples and Docker Compose.
:::

:::{grid-item-card} ⚙️ Configuration Reference
:link: configuration
:link-type: doc
:shadow: sm

All connection, queue, exchange, consumer, retry, and pika logging settings — with types and defaults.
:::

:::{grid-item-card} 🏗️ Architecture
:link: architecture
:link-type: doc
:shadow: sm

Thread-safe connections, message persistence, automatic retries, and queue naming strategy.
:::
::::

---

Part of the **[Pynenc](https://pynenc.readthedocs.io/) ecosystem** ·
[Redis Plugin](https://pynenc-redis.readthedocs.io/) ·
[MongoDB Plugin](https://pynenc-mongodb.readthedocs.io/)

```{toctree}
:hidden:
:maxdepth: 2
:caption: RabbitMQ Plugin

installation
configuration
architecture
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: API Reference

apidocs/index.rst
```

```{toctree}
:hidden:
:caption: Pynenc Ecosystem

Pynenc Docs <https://pynenc.readthedocs.io/>
Redis Plugin <https://pynenc-redis.readthedocs.io/>
MongoDB Plugin <https://pynenc-mongodb.readthedocs.io/>
```
