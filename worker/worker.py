
import os
import json
import time
from datetime import datetime, timezone

import pika
from pymongo import MongoClient
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB = os.getenv("MONGO_DB", "ipa2026_db")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
routers = db["routers"]

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "rabbitmq")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "router_jobs")


def get_router_interfaces(router):
    """Connect to a Cisco router and retrieve interface status."""
    device = {
        "device_type": "cisco_ios",
        "host": router["ip"],
        "username": router["username"],
        "password": router["password"],
        "conn_timeout": 10,
        "auth_timeout": 10,
        "banner_timeout": 10,
    }

    with ConnectHandler(**device) as connection:
        output = connection.send_command(
            "show ip interface brief",
            read_timeout=30,
            use_textfsm=True,
        )

    # TextFSM normally returns a list of dictionaries.
    if isinstance(output, list):
        return output

    # Fallback if TextFSM parsing is unavailable.
    return [{"raw_output": str(output)}]


def process_message(channel, method, properties, body):
    try:
        message = json.loads(body)
        ip = message.get("ip")

        if not ip:
            print("Job skipped: missing router IP", flush=True)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        router = routers.find_one({"ip": ip})

        if not router:
            print(f"Router {ip} not found in MongoDB", flush=True)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        interfaces = get_router_interfaces(router)
        now = datetime.now(timezone.utc)

        snapshot = {
            "timestamp": now,
            "interfaces": interfaces,
        }

        routers.update_one(
            {"_id": router["_id"]},
            {
                "$set": {
                    "interfaces": interfaces,
                    "interface_status_updated_at": now,
                },
                "$push": {
                    "history": {
                        "$each": [snapshot],
                        "$position": 0,
                        "$slice": 3,
                    }
                },
            },
        )

        print(
            f"Saved {len(interfaces)} interfaces for {ip} at {now.isoformat()}",
            flush=True,
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except NetmikoAuthenticationException as exc:
        print(f"SSH authentication failed: {exc}", flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except NetmikoTimeoutException as exc:
        print(f"Router SSH timeout: {exc}", flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as exc:
        print(f"Job processing error: {exc}", flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    while True:
        try:
            credentials = pika.PlainCredentials(
                RABBITMQ_USER,
                RABBITMQ_PASSWORD,
            )

            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=5672,
                virtual_host="/",
                credentials=credentials,
                heartbeat=60,
                blocked_connection_timeout=30,
            )

            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            channel.queue_declare(
                queue=RABBITMQ_QUEUE,
                durable=True,
            )

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=RABBITMQ_QUEUE,
                on_message_callback=process_message,
            )

            print(
                f"Worker connected to RabbitMQ at {RABBITMQ_HOST}; "
                f"listening on {RABBITMQ_QUEUE}",
                flush=True,
            )

            channel.start_consuming()

        except Exception as exc:
            print(f"Worker connection error: {exc}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
