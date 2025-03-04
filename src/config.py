import os
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()  # Load environment variables from .env file

logger = logging.getLogger(__name__) # Get logger for config module

# --- Neo4j Database Settings ---
NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD: Optional[str] = os.getenv("NEO4J_PASSWORD")

# --- LLM Settings (LM Studio) ---
LLM_API_BASE: str = os.getenv("LLM_API_BASE", "http://localhost:1234/v1")
LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY")
LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "qwen2.5-0.5b-instruct")

# --- Game Settings ---
MAX_CORAG_ITERATIONS: int = int(os.getenv("MAX_CORAG_ITERATIONS", "5"))
DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

# --- Debug and Development Flags ---
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true" # More robust boolean conversion

# --- Input Validation and Error Handling ---
def validate_config():
    """Validates that required environment variables are set."""
    errors = []
    if not NEO4J_PASSWORD:
        errors.append("NEO4J_PASSWORD environment variable is not set.")
    if not LLM_API_KEY:
        errors.append("LLM_API_KEY environment variable is not set.")

    if errors:
        error_message = "Configuration Error(s) detected:\n" + "\n".join(errors)
        logger.error(error_message) # Log detailed error message
        raise ValueError(error_message) # Raise ValueError to halt startup

# --- Configuration Loading and Validation ---
if __name__ != "__main__": # Only validate when imported, not when run directly
    validate_config()
else:
    # Optional: Print configuration when running config.py directly (for debugging)
    print("Current Configuration:")
    print(f"NEO4J_URI: {NEO4J_URI}")
    print(f"NEO4J_USER: {NEO4J_USER}")
    print(f"LLM_API_BASE: {LLM_API_BASE}")
    print(f"LLM_MODEL_NAME: {LLM_MODEL_NAME}")
    print(f"MAX_CORAG_ITERATIONS: {MAX_CORAG_ITERATIONS}")
    print(f"DEFAULT_TEMPERATURE: {DEFAULT_TEMPERATURE}")
    print(f"DEBUG_MODE: {DEBUG_MODE}")
    if NEO4J_PASSWORD: # Don't print password if set
        print("NEO4J_PASSWORD: Set (but not displayed)")
    else:
        print("NEO4J_PASSWORD: Not Set")
    if LLM_API_KEY: # Don't print API Key if set
        print("LLM_API_KEY: Set (but not displayed)")
    else:
        print("LLM_API_KEY: Not Set")


# --- IMPORTANT REMINDER ---
# - DO NOT hardcode sensitive values directly in your code or Dockerfile.
# - Use environment variables and securely manage your .env file (gitignore it!).