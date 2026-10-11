from collections.abc import Sequence
from functools import cached_property
from hashlib import sha256
from typing import TYPE_CHECKING

from pynenc.broker.base_broker import BaseBroker
from pynenc.conf.config_broker import MAX_PRIORITY, MIN_PRIORITY, validate_priority
from pynenc.identifiers.invocation_id import InvocationId

from pynenc_rabbitmq.conf.config_broker import ConfigBrokerRabbitMq
from pynenc_rabbitmq.util.rabbitmq_client import PynencRabbitMqClient

if TYPE_CHECKING:
    from pynenc.app import Pynenc

    from pynenc_rabbitmq.util.rabbitmq_queue_mng import QueueManager


class RabbitMqBroker(BaseBroker):
    """
    A RabbitMq-based implementation of the broker for cross-process coordination.

    Uses RabbitMq queues for cross-process message coordination and implements
    all required abstract methods from BaseBroker. Connection retry with exponential
    backoff is handled automatically at the queue manager level.
    """

    MAX_RABBITMQ_PRIORITY = 255

    def __init__(self, app: "Pynenc") -> None:
        super().__init__(app)
        self._client = PynencRabbitMqClient.get_instance(self.conf)

    @cached_property
    def conf(self) -> ConfigBrokerRabbitMq:
        return ConfigBrokerRabbitMq(
            config_values=self.app.config_values,
            config_filepath=self.app.config_filepath,
        )

    @staticmethod
    def _app_queue_namespace(app_id: str) -> str:
        """Return a compact stable namespace for an application ID."""
        return sha256(app_id.encode()).hexdigest()[:16]

    def _rabbitmq_queue_name(self, queue_name: str) -> str:
        """Return the app-isolated physical name for a logical queue."""
        app_namespace = self._app_queue_namespace(self.app.app_id)
        return f"{self.conf.rabbitmq_queue_prefix}_{app_namespace}_broker_{queue_name}"

    @cached_property
    def _message_queues(self) -> dict[str, "QueueManager"]:
        """Get queue managers for all configured broker queues."""
        return {
            name: self._client.get_queue(
                self._rabbitmq_queue_name(name),
                max_priority=self.MAX_RABBITMQ_PRIORITY,
            )
            for name in self.conf.queues
        }

    def _message_queue(self, queue_name: str) -> "QueueManager":
        """Return a queue manager, creating it lazily for dynamic queues."""
        if queue_name not in self._message_queues:
            self._message_queues[queue_name] = self._client.get_queue(
                self._rabbitmq_queue_name(queue_name),
                max_priority=self.MAX_RABBITMQ_PRIORITY,
            )
        return self._message_queues[queue_name]

    @classmethod
    def _priority_rank(cls, priority: float) -> int:
        """Map Pynenc's float range to RabbitMQ's native integer range."""
        validated = validate_priority(priority, label="RabbitMQ priority")
        normalized = (validated - MIN_PRIORITY) / (MAX_PRIORITY - MIN_PRIORITY)
        return round(normalized * cls.MAX_RABBITMQ_PRIORITY)

    def send_message(
        self, invocation_id: InvocationId, queue_name: str, priority: float
    ) -> None:
        """Send a message (invocation) to the queue."""
        published = self._message_queue(queue_name).publish_message(
            str(invocation_id),
            priority=self._priority_rank(priority),
        )
        if not published:
            raise RuntimeError(
                f"RabbitMQ rejected invocation {invocation_id} for queue {queue_name}"
            )

    def _route_invocation(
        self, invocation_id: InvocationId, queue_name: str, priority: float
    ) -> None:
        """Route a single invocation by sending it to the message queue."""
        self.send_message(invocation_id, queue_name, priority)

    def _route_invocations(
        self,
        invocation_ids: Sequence[InvocationId],
        queue_name: str,
        priority: float,
    ) -> None:
        """Route multiple invocations by sending them to the message queue."""
        if not invocation_ids:
            return

        self.app.logger.info(f"Routing {len(invocation_ids)} invocations")

        for invocation_id in invocation_ids:
            self.send_message(invocation_id, queue_name, priority)

    def retrieve_invocation(self, queue_name: str | None = None) -> InvocationId | None:
        """
        Retrieve a single invocation from the queue.

        :return: The next DistributedInvocation in the queue, or None if empty.
        """
        queue = self.conf.queues[0] if queue_name is None else queue_name
        self._validate_queue_names((queue,))
        if msg := self._message_queue(queue).consume_message():
            return InvocationId(msg)
        return None

    def count_invocations(self, queue_names: Sequence[str] | None = None) -> int:
        """Count the number of invocations in the queue."""
        queues = self.conf.queues if queue_names is None else tuple(queue_names)
        self._validate_queue_names(queues)
        return sum(self._message_queue(queue).get_message_count() for queue in queues)

    def purge(self) -> None:
        """Clear all messages from the queue."""
        for queue in self._message_queues.values():
            queue.purge_queue()
