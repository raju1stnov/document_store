import os
import json
from kafka import KafkaConsumer
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

# Get Kafka configuration and Qdrant connection details from environment variables.
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

consumer = KafkaConsumer(
    "chunks",
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="embedder-group"
)

# Initialize your embedding model.
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize the Qdrant client.
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
COLLECTION_NAME = "documents"

# Create the collection if it does not exist.
existing_collections = [c.name for c in qdrant_client.get_collections().collections]
if COLLECTION_NAME not in existing_collections:
    qdrant_client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "size": 384,  # Dimension for 'all-MiniLM-L6-v2'
            "distance": "Cosine"
        }
    )

def upsert_embedding(doc_id, embedding, payload):
    point = PointStruct(
        id=doc_id,
        vector=embedding.tolist(),
        payload=payload
    )
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point])

if __name__ == "__main__":
    for msg in consumer:
        try:
            data = msg.value
            print(f"[Embedder] Embedding chunk {data.get('chunk_index')} of file {data.get('file_name')}")
            chunk_text = data.get("chunk_text", "")
            embedding = model.encode(chunk_text).tolist()
            payload = {
                "file_name": data.get("file_name"),
                "saved_filename": data.get("saved_filename"),
                "chunk_index": data.get("chunk_index"),
                "chunk_text": chunk_text
            }
            # Create a unique identifier for the chunk.
            doc_id = f"{data.get('file_name')}_{data.get('chunk_index')}"
            upsert_embedding(doc_id, embedding, payload)
        except Exception as e:
            print(f"[Embedder] Error processing chunk: {e}")