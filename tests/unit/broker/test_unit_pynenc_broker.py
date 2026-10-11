"""Unit tests for Pynenc broker with RabbitMQ implementation."""

from typing import TYPE_CHECKING

from pynenc_tests.unit.broker.all_tests import *
from pynenc_tests.unit.broker.test_broker_all_instances import (
    bind_task,
    default_task,
    payment_task,
    report_task,
    urgent_payment_task,
)

if TYPE_CHECKING:
    from pynenc import Pynenc
    from pynenc.invocation import DistributedInvocation


def test_rabbitmq_named_queue_filtering_and_priority(app_instance: "Pynenc") -> None:
    """RabbitMQ creates one physical queue per logical queue and applies priority."""
    app_instance.config_values.update(
        {
            "queues": ("default", "payments", "reports"),
            "priority_rules": (
                {
                    "task_id": f"{payment_task.task_id.key}",
                    "priority": 50.0,
                },
                {
                    "task_id": f"{report_task.task_id.key}",
                    "priority": -10.0,
                },
            ),
        }
    )
    default = bind_task(app_instance, default_task)
    payment = bind_task(app_instance, payment_task)
    urgent = bind_task(app_instance, urgent_payment_task)
    report = bind_task(app_instance, report_task)

    default_inv: DistributedInvocation = default()  # type: ignore
    payment_inv: DistributedInvocation = payment()  # type: ignore
    urgent_inv: DistributedInvocation = urgent()  # type: ignore
    report_inv: DistributedInvocation = report()  # type: ignore

    assert app_instance.broker.count_invocations(("default",)) == 1
    assert app_instance.broker.count_invocations(("payments",)) == 2
    assert app_instance.broker.count_invocations(("reports",)) == 1

    assert (
        app_instance.broker.retrieve_invocation("payments") == urgent_inv.invocation_id
    )
    assert (
        app_instance.broker.retrieve_invocation("payments") == payment_inv.invocation_id
    )
    assert (
        app_instance.broker.retrieve_invocation("reports") == report_inv.invocation_id
    )
    assert (
        app_instance.broker.retrieve_invocation("default") == default_inv.invocation_id
    )


def test_rabbitmq_priority_normalization_boundaries(app_instance: "Pynenc") -> None:
    broker = app_instance.broker

    assert broker._priority_rank(-100.0) == 0
    assert broker._priority_rank(0.0) == 128
    assert broker._priority_rank(100.0) == 255


def test_rabbitmq_queue_names_are_isolated_by_app_id(
    app_instance: "Pynenc",
) -> None:
    """Apps sharing a RabbitMQ virtual host must not consume each other's work."""
    broker = app_instance.broker

    assert broker._app_queue_namespace("first-app") != broker._app_queue_namespace(
        "second-app"
    )
    assert broker._app_queue_namespace(app_instance.app_id) in (
        broker._rabbitmq_queue_name("default")
    )
    assert broker._rabbitmq_queue_name("default").endswith("_broker_default")
