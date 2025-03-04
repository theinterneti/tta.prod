import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()  # Load environment variables from .env file

# --- Neo4j Database Settings ---
NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD: Optional[str] = os.getenv("NEO4J_PASSWORD")  # Don't provide a default

# --- LLM Settings (LM Studio) ---
LLM_API_BASE: str = os.getenv("LLM_API_BASE", "http://localhost:1234/v1")
LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY")  # No default; required in production
LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "qwen2.5-0.5b-instruct")

# --- Game Settings ---
MAX_CORAG_ITERATIONS: int = int(os.getenv("MAX_CORAG_ITERATIONS", "5"))  # Use int() for type safety
DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7")) # Use float() for type safety

# --- Input Validation (Optional but Recommended) ---
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is required.")
if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY environment variable is required.")