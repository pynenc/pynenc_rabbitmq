from dataclasses import dataclass
from typing import Any


@dataclass
class QueueSpec:
    """Specification for creating a RabbitMq queue."""

    name: str
    durable: bool = True
    exclusive: bool = False
    auto_delete: bool = False
    arguments: dict[str, Any] | None = None
    max_priority: int | None = None
    exchange: str = ""  # Empty string means default exchange
    routing_key: str | None = None  # If None, use queue name

    def __post_init__(self) -> None:
        """Set routing_key to queue name if not specified."""
        if self.routing_key is None:
            self.routing_key = self.name

    @property
    def declaration_arguments(self) -> dict[str, Any] | None:
        """RabbitMQ queue declaration arguments."""
        args = dict(self.arguments or {})
        if self.max_priority is not None:
            args["x-max-priority"] = self.max_priority
        return args or None
