import json
import os
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "rabbitmq")


def send_router(router):
    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            credentials=credentials,
            heartbeat=30,
            connection_attempts=5,
            retry_delay=2
        )
    )

    channel = connection.channel()
    channel.exchange_declare(
        exchange="jobs",
        exchange_type="direct",
        durable=True
    )
    channel.queue_declare(queue="router_jobs", durable=True)
    channel.queue_bind(
        queue="router_jobs",
        exchange="jobs",
        routing_key="check_interfaces"
    )

    message = json.dumps(router, default=str)

    channel.basic_publish(
        exchange="jobs",
        routing_key="check_interfaces",
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json"
        )
    )

    print(f"Sent router: {router.get('ip', 'unknown')}", flush=True)
    connection.close()
