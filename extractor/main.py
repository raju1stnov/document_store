import os
import json
from kafka import KafkaConsumer, KafkaProducer
from docling.parser import extract_text

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

consumer = KafkaConsumer(
    "raw_files",
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="extractor-group"
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

if __name__ == "__main__":
    for msg in consumer:
        try:
            data = msg.value
            print(f"[Extractor] Processing file: {data['file_name']}")
            # Use docling to extract text from the local file.
            text = extract_text(data["file_path"])
            new_message = {
                "file_name": data["file_name"],
                "saved_filename": data["saved_filename"],
                "content": text
            }
            producer.send("extracted_docs", new_message)
            producer.flush()
        except Exception as e:
            print(f"[Extractor] Error processing {data.get('file_name')}: {e}")