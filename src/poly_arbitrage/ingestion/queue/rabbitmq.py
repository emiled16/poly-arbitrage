from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pika


@dataclass(slots=True)
class RabbitMqQueue:
    url: str
    queue_name: str
    dead_letter_exchange: str
    dead_letter_queue_name: str

    def publish(self, job_id: str) -> None:
        connection = pika.BlockingConnection(pika.URLParameters(self.url))
        try:
            channel = connection.channel()
            self._declare_queue(channel)
            channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps({"job_id": job_id}).encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )
        finally:
            connection.close()

    def consume(self, handler: Callable[[str], None]) -> None:
        connection = pika.BlockingConnection(pika.URLParameters(self.url))
        channel = connection.channel()
        self._declare_queue(channel)
        channel.basic_qos(prefetch_count=1)

        def on_message(channel: Any, method: Any, properties: Any, body: bytes) -> None:
            del properties
            payload = json.loads(body.decode("utf-8"))
            job_id = payload["job_id"]
            try:
                handler(job_id)
            except Exception:
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            channel.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=self.queue_name, on_message_callback=on_message)
        channel.start_consuming()

    def _declare_queue(self, channel: Any) -> None:
        channel.exchange_declare(
            exchange=self.dead_letter_exchange,
            exchange_type="direct",
            durable=True,
        )
        channel.queue_declare(queue=self.dead_letter_queue_name, durable=True)
        channel.queue_bind(
            exchange=self.dead_letter_exchange,
            queue=self.dead_letter_queue_name,
            routing_key=self.queue_name,
        )
        channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={"x-dead-letter-exchange": self.dead_letter_exchange},
        )
