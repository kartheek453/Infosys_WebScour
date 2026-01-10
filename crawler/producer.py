# ================================
# TASK 6: PRODUCER (URL PUBLISHER)
# ================================

import pika

SEED_URLS = [
    "https://coursera.org",
    "https://example.com"
]

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost")
)
channel = connection.channel()

# Create queue
channel.queue_declare(queue="url_queue", durable=True)

# Send seed URLs
for url in SEED_URLS:
    channel.basic_publish(
        exchange="",
        routing_key="url_queue",
        body=url
    )
    print(f"[Producer] Sent URL: {url}")

connection.close()
