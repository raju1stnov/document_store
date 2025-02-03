import os
import json
import uuid
import shutil
import time
from typing import List

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from kafka import KafkaProducer
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility, MilvusException

app = FastAPI(
    title="Document Store API",
    description="Upload documents and search the vector store",
    version="1.0"
)

# Environment variables for Kafka and Milvus
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = "documents"  # Must match the embedder service

# Initialize Kafka producer for publishing file upload events
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Retry logic: wait for Milvus to be available.
print("Trying to connect to Milvus in API...")
while True:
    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        print("API connected to Milvus!")
        break
    except Exception as e:
        print("Milvus not ready in API, waiting 10 seconds...", e)
        time.sleep(10)

# Assume the collection already exists (created by the embedder)
collection = Collection(name=COLLECTION_NAME)

# Load embedding model for search queries
model = SentenceTransformer('all-MiniLM-L6-v2')

# Ensure uploads folder exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Pydantic model for search results
class SearchResult(BaseModel):
    id: str
    distance: float
    payload: dict

@app.get("/", summary="API Root")
async def root():
    return {"message": "Welcome to the Document Store API. Visit /docs for Swagger UI."}

@app.post("/upload", summary="Upload Document")
async def upload_document(file: UploadFile = File(...)):
    unique_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{unique_id}{file_ext}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File saving error: {e}")

    message = {
        "file_name": file.filename,
        "saved_filename": saved_filename,
        "file_path": file_path
    }
    try:
        producer.send("raw_files", message)
        producer.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Kafka: {e}")

    return {"message": "File uploaded successfully", "file": file.filename}

@app.get("/search", response_model=List[SearchResult], summary="Search Documents")
async def search_documents(
    query: str = Query(..., description="The search query text"),
    limit: int = Query(5, description="Number of search results to return")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    query_vector = model.encode(query).tolist()

    try:
        search_results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=limit,
            expr=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching Milvus: {e}")

    results = []
    for hits in search_results:
        for hit in hits:
            payload = json.loads(hit.entity.get("payload", "{}"))
            results.append(SearchResult(
                id=str(hit.entity.get("doc_id")),
                distance=hit.distance,
                payload=payload
            ))
    return results