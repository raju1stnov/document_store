import os
import time
import json
from kafka import KafkaConsumer
from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
    MilvusException,
)
import numpy as np

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

# Retry logic: wait for Milvus to be available.
print("Trying to connect to Milvus...")
while True:
    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        print("Connected to Milvus!")
        break
    except Exception as e:
        print("Milvus not ready yet, waiting 10 seconds...", e)
        time.sleep(10)

COLLECTION_NAME = "documents"

# Create the collection if it does not exist.
if not utility.has_collection(COLLECTION_NAME):
    doc_id_field = FieldSchema(
        name="doc_id", dtype=DataType.VARCHAR, max_length=128, is_primary=True, auto_id=False
    )
    embedding_field = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
    payload_field = FieldSchema(name="payload", dtype=DataType.VARCHAR, max_length=1024)
    schema = CollectionSchema(
        fields=[doc_id_field, embedding_field, payload_field],
        description="Document embeddings",
    )
    collection = Collection(name=COLLECTION_NAME, schema=schema)
else:
    collection = Collection(name=COLLECTION_NAME)

consumer = KafkaConsumer(
    "chunks",
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="embedder-group"
)

# Initialize embedding model.
model = SentenceTransformer('all-MiniLM-L6-v2')

def upsert_embedding(doc_id, embedding, payload):
    # Convert payload dictionary to JSON string.
    payload_str = json.dumps(payload)
    data = [
        [doc_id],
        [embedding],
        [payload_str]
    ]
    collection.insert(data)

if __name__ == "__main__":
    for msg in consumer:
        try:
            data = msg.value
            chunk_text_value = data.get("chunk_text", "")
            print(f"[Embedder] Embedding chunk {data.get('chunk_index')} of file {data.get('file_name')}")
            embedding = model.encode(chunk_text_value).tolist()
            payload = {
                "file_name": data.get("file_name"),
                "saved_filename": data.get("saved_filename"),
                "chunk_index": data.get("chunk_index"),
                "chunk_text": chunk_text_value
            }
            doc_id = f"{data.get('file_name')}_{data.get('chunk_index')}"
            upsert_embedding(doc_id, embedding, payload)
        except Exception as e:
            print(f"[Embedder] Error processing chunk: {e}")
