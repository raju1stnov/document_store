import os
import json
import uuid
import shutil
from typing import List

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from kafka import KafkaProducer
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

app = FastAPI(
    title="Document Store API",
    description="Upload documents and search the vector store",
    version="1.0"
)

# Get configuration from environment variables.
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "documents"  # This should match the embedder’s collection name.

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

model = SentenceTransformer('all-MiniLM-L6-v2')

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class SearchResult(BaseModel):
    id: str
    score: float
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
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching Qdrant: {e}")
    results = []
    for point in search_results:
        results.append(SearchResult(
            id=str(point.id),
            score=point.score,
            payload=point.payload
        ))
    return results