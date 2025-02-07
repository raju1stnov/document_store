import os
import json
import time
from io import BytesIO

from kafka import KafkaConsumer, KafkaProducer, errors as kafka_errors
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter

# Retrieve Kafka broker address from environment variables.
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Retry loop to create a Kafka consumer.
consumer = None
while consumer is None:
    try:
        consumer = KafkaConsumer(
            "raw_files",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            group_id="extractor-group"
        )
        print("Connected to Kafka broker.", flush=True)
    except kafka_errors.NoBrokersAvailable as e:
        print("Kafka not ready, waiting 10 seconds...", e, flush=True)
        time.sleep(10)

# Create a Kafka producer.
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Debug cache directory
print(f"HF_HOME: {os.getenv('HF_HOME')}", flush=True)
print(f"Cache contents: {os.listdir(os.getenv('HF_HOME'))}", flush=True)

try:
    print("Initializing DocumentConverter...", flush=True)
    converter = DocumentConverter()  # No need for `cache_dir`, rely on HF_HOME
    print("DocumentConverter initialized successfully.", flush=True)
except Exception as e:
    print(f"Error initializing DocumentConverter: {e}", flush=True)

# Process incoming Kafka messages.
if __name__ == "__main__":
    for msg in consumer:
        try:
            data = msg.value
            print(f"[Extractor] Processing file: {data['file_name']}", flush=True)
            
            # Read the file as binary.
            with open(data["file_path"], "rb") as f:
                file_bytes = f.read()

            # Create a BytesIO stream for the DocumentStream.
            buf = BytesIO(file_bytes)
            
            # Create a DocumentStream object using the file name and stream.
            source = DocumentStream(name=data["file_name"], stream=buf)
            
            # Convert the document using the high-level DocumentConverter.
            result = converter.convert(source)
            
            # Extract text from the converted document.
            text = result.document.export_to_markdown()
            
            # Prepare a new message with the extracted content.
            new_message = {
                "file_name": data["file_name"],
                "saved_filename": data["saved_filename"],
                "content": text
            }
            
            # Send the new message to the 'extracted_docs' Kafka topic.
            producer.send("extracted_docs", new_message)
            producer.flush()
            
        except Exception as e:
            print(f"[Extractor] Error processing {data.get('file_name')}: {e}", flush=True)