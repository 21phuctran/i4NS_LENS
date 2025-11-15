"""
Configuration for i4NS LENS (Lessons Learned Enhancement System)
Offline deployment configuration for Navy ships
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCTRINES_DIR = DATA_DIR / "doctrines"
MISSION_LOGS_DIR = DATA_DIR / "mission_logs"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Create directories if they don't exist
DOCTRINES_DIR.mkdir(parents=True, exist_ok=True)
MISSION_LOGS_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# Model configuration (for offline use)
# Using local embeddings model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Small, fast, offline

# LLM configuration - using local model via Ollama or LlamaCPP
USE_LOCAL_LLM = True
LOCAL_LLM_MODEL = "llama2"  # Can be changed to any model available via Ollama

# Vector store configuration
VECTOR_STORE_TYPE = "faiss"  # Offline-friendly
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# API configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# Logging
LOG_FILE = BASE_DIR / "logs" / "application.log"
LOG_FILE.parent.mkdir(exist_ok=True)
