import os
import json
import time
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from kafka import KafkaProducer, errors as kafka_errors
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

app = FastAPI(
    title="Document Store API",
    description="Upload documents and search the vector store",
    version="1.0"
)

# Environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Wait for Kafka to be ready before initializing the producer.
producer = None
while producer is None:
    try:
        print("Attempting to connect to Kafka...", flush=True)
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        print("Connected to Kafka successfully.", flush=True)
    except kafka_errors.NoBrokersAvailable as e:
        print("Kafka not ready, retrying in 10 seconds...", e, flush=True)
        time.sleep(10)

# Initialize Qdrant client and SentenceTransformer model.
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer('all-MiniLM-L6-v2')

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class SearchResult(BaseModel):
    id: str
    score: float
    payload: dict

@app.get("/", summary="API Root")
async def root():
    return {"message": "Welcome to the Document Store API. Visit /docs for Swagger UI."}

@app.post("/upload", summary="Upload Document")
async def upload_document(file: UploadFile = File(...)):
    import uuid, shutil
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

@app.get("/search", response_model=list[SearchResult], summary="Search Documents")
async def search_documents(
    query: str = Query(..., description="The search query text"),
    limit: int = Query(5, description="Number of search results to return")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    query_vector = model.encode(query).tolist()

    try:
        search_results = qdrant_client.search(
            collection_name="documents",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)