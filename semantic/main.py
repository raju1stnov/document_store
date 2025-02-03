import os
import json
import time
from kafka import KafkaConsumer, KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Retry loop for Kafka consumer creation
while True:
    try:
        consumer = KafkaConsumer(
            "extracted_docs",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            group_id="semantic-group"
        )
        break
    except Exception as e:
        print("Kafka not ready for semantic service, retrying in 10 seconds...", e)
        time.sleep(10)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def create_semantic_representation(text):
    return text.lower()

if __name__ == "__main__":
    for msg in consumer:
        try:
            data = msg.value
            print(f"[Semantic] Processing file: {data['file_name']}")
            semantic_content = create_semantic_representation(data["content"])
            data["semantic_content"] = semantic_content
            producer.send("semantic_docs", data)
            producer.flush()
        except Exception as e:
            print(f"[Semantic] Error processing {data.get('file_name')}: {e}")
