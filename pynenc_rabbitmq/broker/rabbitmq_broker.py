from functools import cached_property
from typing import TYPE_CHECKING

from pynenc.broker.base_broker import BaseBroker

from pynenc_rabbitmq.conf.config_broker import ConfigBrokerRabbitMq
from pynenc_rabbitmq.util.rabbitmq_client import PynencRabbitMqClient

if TYPE_CHECKING:
    from pynenc.app import Pynenc

    from pynenc_rabbitmq.util.rabbitmq_queue_mng import QueueManager


class RabbitMqBroker(BaseBroker):
    """
    A RabbitMq-based implementation of the broker for cross-process coordination.

    Uses RabbitMq queues for cross-process message coordination and implements
    all required abstract methods from BaseBroker.
    """

    def __init__(self, app: "Pynenc") -> None:
        super().__init__(app)
        self._client = PynencRabbitMqClient.get_instance(self.conf)

    @cached_property
    def conf(self) -> ConfigBrokerRabbitMq:
        return ConfigBrokerRabbitMq(
            config_values=self.app.config_values,
            config_filepath=self.app.config_filepath,
        )

    @cached_property
    def _message_queue(self) -> "QueueManager":
        """Get the message queue manager."""
        queue_name = f"{self.conf.rabbitmq_queue_prefix}_broker_messages"
        return self._client.get_queue(queue_name)

    def send_message(self, invocation_id: str) -> None:
        """Send a message (invocation) to the queue."""
        success = self._message_queue.publish_message(invocation_id)
        if not success:
            raise RuntimeError(f"Failed to send message for invocation {invocation_id}")

    def route_invocation(self, invocation_id: str) -> None:
        """Route a single invocation by sending it to the message queue."""
        self.send_message(invocation_id)

    def route_invocations(self, invocation_ids: list[str]) -> None:
        """Route multiple invocations by sending them to the message queue."""
        if not invocation_ids:
            return

        self.app.logger.warning(
            f"Routing {len(invocation_ids)} invocations: {invocation_ids}"
        )

        for invocation_id in invocation_ids:
            self.send_message(invocation_id)

    def retrieve_invocation(self) -> str | None:
        """
        Retrieve a single invocation from the queue.

        :return: The next DistributedInvocation in the queue, or None if empty.
        """
        return self._message_queue.consume_message()

    def count_invocations(self) -> int:
        """Count the number of invocations in the queue."""
        return self._message_queue.get_message_count()

    def purge(self) -> None:
        """Clear all messages from the queue."""
        self._message_queue.purge_queue()
