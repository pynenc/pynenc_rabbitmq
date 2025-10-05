"""
RabbitMQ plugin builder extensions for Pynenc.

This module contains the RabbitMQ-specific builder methods for the pynenc-rabbitmq plugin.

Key components:
- RabbitMqBuilderPlugin: Plugin class that registers RabbitMQ methods
- rabbitmq(): Main method for RabbitMQ stack configuration
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pynenc.builder import PynencBuilder


class RabbitMqBuilderPlugin:
    """RabbitMQ plugin that provides builder methods for RabbitMQ backend configuration."""

    @staticmethod
    def register_builder_methods(builder_class: type["PynencBuilder"]) -> None:
        """
        Register RabbitMQ builder methods with PynencBuilder.

        :param type["PynencBuilder"] builder_class: The PynencBuilder class to extend
        """
        builder_class.register_plugin_method("rabbitmq_broker", rabbitmq_broker)
        builder_class.register_plugin_validator(validate_rabbitmq_config)


def rabbitmq_broker(
    builder: "PynencBuilder",
    host: str | None = None,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    virtual_host: str | None = None,
    queue_prefix: str | None = None,
    exchange_name: str | None = None,
    exchange_type: str | None = None,
) -> "PynencBuilder":
    """
    Configure RabbitMQ components for the Pynenc application.

    Sets up RabbitMQ as the backend for broker and related components.
    Only explicitly provided parameters are set; defaults are handled in ConfigRabbitMq.

    :param builder: The PynencBuilder instance
    :param host: RabbitMQ host
    :param port: RabbitMQ port
    :param username: RabbitMQ username
    :param password: RabbitMQ password
    :param virtual_host: RabbitMQ virtual host
    :param queue_prefix: Prefix for RabbitMQ queues
    :param exchange_name: Name of the RabbitMQ exchange
    :param exchange_type: Type of the RabbitMQ exchange
    :return: The builder instance for method chaining
    """
    if host:
        builder._config["rabbitmq_host"] = host
    if port:
        builder._config["rabbitmq_port"] = port
    if username:
        builder._config["rabbitmq_username"] = username
    if password:
        builder._config["rabbitmq_password"] = password
    if virtual_host:
        builder._config["rabbitmq_virtual_host"] = virtual_host
    if queue_prefix:
        builder._config["rabbitmq_queue_prefix"] = queue_prefix
    if exchange_name:
        builder._config["rabbitmq_exchange_name"] = exchange_name
    if exchange_type:
        builder._config["rabbitmq_exchange_type"] = exchange_type

    builder._config["broker_cls"] = "RabbitMqBroker"
    builder._plugin_components.add("rabbitmq")
    builder._using_memory_components = False
    return builder


def validate_rabbitmq_config(config: dict[str, Any]) -> None:
    """
    Validate RabbitMQ plugin configuration.

    Ensures that RabbitMQ broker has required connection settings.

    :param config: Configuration dictionary to validate
    :raises ValueError: If RabbitMQ broker is configured without host
    """
    uses_rabbitmq = config.get("broker_cls") == "RabbitMqBroker"
    has_rabbitmq_host = bool(config.get("rabbitmq_host"))

    if uses_rabbitmq and not has_rabbitmq_host:
        raise ValueError(
            "RabbitMQ components require connection configuration. "
            "Set rabbitmq_host or call rabbitmq() with connection parameters."
        )
