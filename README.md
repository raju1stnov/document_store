Pre-Download the Models on Your Host

1. **Set Up a Temporary Environment Variable for the Cache**
   On your host machine, set the `HF_HOME` environment variable to a local folder where you want to store the models. For example, you can use your project folder’s `hf_cache` directory. (You can set this in your shell or directly in your Python script.)
2. **Create a Preload Script**
   Create a file called `preload_docling.py`
3. After running, check that a folder named `hf_cache` now exists in your project directory and that it contains subdirectories (e.g., under `hf_cache/hub/models--ds4sd--docling-models`) with the downloaded model artifacts.
4. Ingesting Files into Your Document Store
   Using the API’s Upload Endpoint
   Document store API exposes a /upload endpoint.
   You can use the Swagger UI (available at http://localhost:8000/docs) or a tool like Postman or curl to upload the files.

Using Curl Example
Open a terminal and run a command similar to this (repeat for each file):
curl -F "file=@/path/to/Healthcare_Contract_1.docx" http://localhost:8000/upload

Using Swagger UI
Open your browser and navigate to http://localhost:8000/docs.
Find the POST /upload endpoint.
Click on it, then click Try it out.
Choose your file and click Execute.
Repeat the upload for all your sample files.

2. Verifying Ingestion and Testing the Flow

Check Kafka:
Open Kafkadrop at http://localhost:9000 to verify that messages are being published to the raw_files topic, then processed through subsequent topics (e.g., extracted_docs).

Check API Logs:
Inspect the logs for your extractor, semantic, chunker, and embedder services to ensure that each stage of the pipeline is processing the files.

Search Test:
After ingestion, use the /search endpoint (available via http://localhost:8000/docs) to perform a test query. For example:
http://localhost:8000/search?query=contract&limit=5
This should return relevant document chunks stored in your Qdrant vector database.

1. Next Steps for RAG and LLM Integration
   Once you have successfully ingested your healthcare/vendor contract documents, next steps might include:

   1. Implementing a Retrieval-Augmented Generation (RAG) Architecture:
      i.Use search endpoint to retrieve relevant document passages based on a user query.
      ii. Feed these passages as context to a language model (LLM) such as GPT/transformer (via an API like OpenAI’s or Hugging Face Transformers).
   2. Transforming Results to CSV:
      i. Once you have your retrieved passages and possibly a generated response, you can use Python (e.g., with the pandas library) to format the results as a CSV file.
      ii. Expose another endpoint (or a separate script) that takes the retrieval output, converts it to CSV, and either returns it as a file download or saves it to disk.

# document_store docker operation syntax

docker-compose down
docker-compose up --build

a. Remove All Stopped Containers
This command removes all containers that are not currently running:
docker container prune -f

b. Remove All Unused Images
This command removes all images that are not used by any containers:
docker image prune -a -f

c. Remove All Unused Volumes
This command removes all volumes that are not referenced by any container:
docker volume prune -f

d. Remove All Unused Networks
This command removes networks not used by any container:
docker network prune -f

e. Remove Everything at Once
If you want to remove all unused containers, images, volumes, and networks in one go, run:
docker system prune -a --volumes -f

2. Removing Specific Containers and Images Manually
   If you want more control, you can list and remove containers and images manually.

a. List All Containers
docker ps -a

b. Stop All Running Containers
docker stop $(docker ps -q)

c. Remove All Containers
docker rm $(docker ps -aq)

d. List All Images
docker images -a

e. Remove All Images
Remove images by their IDs (this example removes all images):
docker rmi $(docker images -q)

Sometimes you may need to add the -f flag to force removal:
docker rmi -f $(docker images -q)
