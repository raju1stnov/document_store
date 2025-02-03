import os
import json
import time
from kafka import KafkaConsumer, KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))

while True:
    try:
        consumer = KafkaConsumer(
            "semantic_docs",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            group_id="chunker-group"
        )
        break
    except Exception as e:
        print("Kafka not ready for chunker service, retrying in 10 seconds...", e)
        time.sleep(10)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def chunk_text(text, size):
    return [text[i:i+size] for i in range(0, len(text), size)]

if __name__ == "__main__":
    for msg in consumer:
        try:
            data = msg.value
            print(f"[Chunker] Chunking file: {data['file_name']}")
            chunks = chunk_text(data.get("semantic_content", ""), CHUNK_SIZE)
            for index, chunk in enumerate(chunks):
                chunk_message = {
                    "file_name": data["file_name"],
                    "saved_filename": data["saved_filename"],
                    "chunk_index": index,
                    "chunk_text": chunk
                }
                producer.send("chunks", chunk_message)
            producer.flush()
        except Exception as e:
            print(f"[Chunker] Error processing {data.get('file_name')}: {e}")
