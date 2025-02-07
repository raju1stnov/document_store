# https://huggingface.co/ds4sd/docling-models

# preload_docling.py
import os
from transformers import AutoModelForTokenClassification, AutoTokenizer
from huggingface_hub import try_to_load_from_cache

# Define the models to be downloaded
models = [
    "ds4sd/docling-models",
    # Add other models if needed
]

# Define the cache directory
cache_dir = "./hf_cache/hub/models--ds4sd--docling-models"

# Ensure the cache directory exists
os.makedirs(cache_dir, exist_ok=True)

# Download and save models
for model_name in models:
    print(f"Downloading model: {model_name}")
    try:
        model = AutoModelForTokenClassification.from_pretrained(model_name, cache_dir=cache_dir)
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        print(f"Model {model_name} downloaded and saved to {cache_dir}")
    except Exception as e:
        print(f"Error downloading model {model_name}: {e}")
        # Check if the model is cached
        try:
            cached_path = try_to_load_from_cache(model_name, "config.json", cache_dir=cache_dir)
            if cached_path:
                print(f"Model {model_name} is already cached at {cached_path}")
            else:
                print(f"Model {model_name} is not cached and could not be downloaded.")
        except Exception as cache_error:
            print(f"Error checking cache for model {model_name}: {cache_error}")

print("All models downloaded successfully.")