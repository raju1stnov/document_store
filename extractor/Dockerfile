# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the persistent cache directory for Hugging Face / Docling.
ENV HF_HOME=/app/hf_cache
ENV TRANSFORMERS_OFFLINE=1
# Ensure that Hugging Face operates offline
ENV HF_HUB_OFFLINE=1   

# Create the cache directory.
RUN mkdir -p ${HF_HOME}

# Set the working directory.
WORKDIR /app

# Copy the requirements file from the extractor folder and install dependencies.
COPY extractor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Preload Docling models during build to prevent downloads at runtime.
RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

# Ensure that models are properly cached.
RUN ls -l ${HF_HOME} && ls -l ${HF_HOME}/hub

# Copy the extractor application code.
COPY extractor/main.py /app/main.py

# Set the command to run the extractor.
CMD ["python", "main.py"]