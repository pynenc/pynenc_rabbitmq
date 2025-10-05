from pynenc.conf.config_broker import ConfigBroker

from pynenc_rabbitmq.conf.config_rabbitmq import ConfigRabbitMq


class ConfigBrokerRabbitMq(ConfigBroker, ConfigRabbitMq):
    """Specific Configuration for the RABBITMQ Broker"""
