# Pynenc RabbitMq Plugin

[![CI](https://github.com/pynenc/pynenc-rabbitmq/actions/workflows/ci.yml/badge.svg)](https://github.com/pynenc/pynenc-rabbitmq/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pynenc/pynenc-rabbitmq/branch/main/graph/badge.svg)](https://codecov.io/gh/pynenc/pynenc-rabbitmq)
[![PyPI version](https://badge.fury.io/py/pynenc-rabbitmq.svg)](https://badge.fury.io/py/pynenc-rabbitmq)
[![Python versions](https://img.shields.io/pypi/pyversions/pynenc-rabbitmq.svg)](https://pypi.org/project/pynenc-rabbitmq/)

RabbitMq state backend plugin for [Pynenc](https://github.com/pynenc/pynenc), providing distributed task state management using RabbitMq as the storage backend.

## Features

- 🚀 **High Performance**: Optimized RabbitMq operations with connection pooling
- 🔒 **Distributed Locking**: RabbitMq-based distributed locks for task coordination
- 🎯 **Type Safe**: Full type hints and mypy compatibility
- 🧪 **Well Tested**: Comprehensive test suite with multiple RabbitMq versions
- 📊 **Production Ready**: Battle-tested configuration options and monitoring

## Quick Start

### Installation

```bash
pip install pynenc-rabbitmq
```

### Basic Usage

```python
from pynenc import Pynenc
from pynenc_rabbitmq import RabbitMqStateBackend

# Create Pynenc app with RabbitMq backend
app = Pynenc().with_state_backend(
    RabbitMqStateBackend.from_uri("rabbitmq://localhost:27017/pynenc")
)

@app.task
def my_task(x: int, y: int) -> int:
    return x + y

# Use your tasks as normal
result = my_task(1, 2)
```

## Configuration

### Connection Configuration

```python
from pynenc_rabbitmq import RabbitMqStateBackend, ConfigRabbitMq

config = ConfigRabbitMq(
    uri="rabbitmq://localhost:27017",
    database_name="my_pynenc_db",
    max_pool_size=100,
    write_concern_w="majority",
    read_preference="primaryPreferred"
)

backend = RabbitMqStateBackend(config)
```

### Environment Variables

You can also configure via environment variables:

```bash
export PYNENC_RABBITMQ_URI="rabbitmq://localhost:27017"
export PYNENC_RABBITMQ_DATABASE="pynenc"
export PYNENC_RABBITMQ_MAX_POOL_SIZE="100"
```

## Documentation

- [Configuration Guide](docs/configuration/index.md)
- [Usage Examples](docs/usage/index.md)
- [Migration Guide](docs/migration/index.md)

## Development

### Setup

1. Clone the repository
2. Install dependencies: `poetry install --with dev`
3. Start RABBITMQ: `docker-compose -f docker/docker-compose.yml up -d`
4. Run tests: `poetry run pytest`

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
