from cistell import ConfigField
from pynenc.conf.config_base import ConfigPynencBase


class ConfigRabbitMq(ConfigPynencBase):
    """
    Configuration for RabbitMQ client connections and messaging.

    This class provides configuration settings for RabbitMQ connections, queues,
    and message handling used throughout the Pynenc system.

    :cvar ConfigField[str] rabbitmq_host:
        The hostname of the RabbitMQ server. Defaults to 'localhost', specifying that
        the RabbitMQ server is expected to be running on the same machine as the client.

    :cvar ConfigField[int] rabbitmq_port:
        The port number on which the RabbitMQ server is listening. Defaults to 5672,
        which is the default AMQP port for RabbitMQ.

    :cvar ConfigField[str] rabbitmq_username:
        The username to use when connecting to the RabbitMQ server. Defaults to 'guest',
        which is the default RabbitMQ username.

    :cvar ConfigField[str] rabbitmq_password:
        The password to use when connecting to the RabbitMQ server. Defaults to 'guest',
        which is the default RabbitMQ password.

    :cvar ConfigField[str] rabbitmq_virtual_host:
        The virtual host to use on the RabbitMQ server. Defaults to '/', which is the
        default virtual host in RabbitMQ. Virtual hosts provide logical grouping and
        separation of resources.

    :cvar ConfigField[str] rabbitmq_queue_prefix:
        The prefix to use for all RabbitMQ queue names. Defaults to 'pynenc'. This helps
        namespace queues and avoid conflicts when multiple applications share a RabbitMQ
        instance.

    :cvar ConfigField[str] rabbitmq_exchange_name:
        The name of the RabbitMQ exchange to use for message routing. Defaults to
        'pynenc.direct'. All messages are published to this exchange.

    :cvar ConfigField[str] rabbitmq_exchange_type:
        The type of RabbitMQ exchange to create. Defaults to 'direct'. Common types are
        'direct', 'topic', 'fanout', and 'headers'. Direct exchanges route messages to
        queues based on exact routing key matches.

    :cvar ConfigField[int] rabbitmq_connection_attempts:
        The maximum number of connection attempts before failing. Defaults to 3.
        The client will retry this many times if the initial connection fails.

    :cvar ConfigField[float] rabbitmq_retry_delay:
        The delay in seconds between connection retry attempts. Defaults to 5.0.
        After a failed connection attempt, the client waits this long before retrying.

    :cvar ConfigField[int] rabbitmq_heartbeat:
        The heartbeat interval in seconds for the RabbitMQ connection. Defaults to 600
        (10 minutes). Heartbeats detect and close broken connections. Set to 0 to disable.

    :cvar ConfigField[int] rabbitmq_prefetch_count:
        The number of unacknowledged messages that can be delivered to a consumer.
        Defaults to 10. This implements QoS (Quality of Service) flow control.

    :cvar ConfigField[int] rabbitmq_message_ttl:
        The message time-to-live in milliseconds. Defaults to 86400000 (24 hours).
        Messages older than this are automatically deleted from queues. Set to 0 to
        disable TTL.

    :cvar ConfigField[bool] rabbitmq_confirm_delivery:
        Whether to enable publisher confirms for reliable message delivery. Defaults to
        True. When enabled, RabbitMQ confirms that messages were successfully received,
        allowing detection of publish failures.
    """

    # Connection settings
    rabbitmq_host = ConfigField("localhost")
    rabbitmq_port = ConfigField(5672)
    rabbitmq_username = ConfigField("guest")
    rabbitmq_password = ConfigField("guest")
    rabbitmq_virtual_host = ConfigField("/")

    # Queue and exchange configuration
    rabbitmq_queue_prefix = ConfigField("pynenc")
    rabbitmq_exchange_name = ConfigField("pynenc.direct")
    rabbitmq_exchange_type = ConfigField("direct")

    # Connection behavior
    rabbitmq_connection_attempts = ConfigField(3)
    rabbitmq_retry_delay = ConfigField(5.0)
    rabbitmq_heartbeat = ConfigField(600)

    # Message handling
    rabbitmq_prefetch_count = ConfigField(10)
    rabbitmq_message_ttl = ConfigField(86400000)  # 24 hours in milliseconds
    rabbitmq_confirm_delivery = ConfigField(True)
