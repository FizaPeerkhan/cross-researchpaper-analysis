# scripts/download_datasets.py

"""Download standard datasets for training/evaluation."""

import os
import json
from loguru import logger
from datasets import load_dataset

DATASETS = {
    "scierc": {
        "name": "scierc",
        "description": "Scientific Entity Recognition and Relation Extraction",
    },
    "scifact": {
        "name": "scifact",
        "description": "Scientific Fact Verification",
    },
}

def download_datasets(output_dir: str = "data/annotations"):
    """Download datasets for training and evaluation."""
    os.makedirs(output_dir, exist_ok=True)
    
    for name, info in DATASETS.items():
        logger.info(f"Downloading {info['description']}...")
        try:
            dataset = load_dataset(name)
            dataset.save_to_disk(os.path.join(output_dir, name))
            logger.info(f"Saved {name} to {output_dir}")
        except Exception as e:
            logger.error(f"Failed to download {name}: {e}")

if __name__ == "__main__":
    download_datasets()