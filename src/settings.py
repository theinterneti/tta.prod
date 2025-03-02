## app settings.py
##Configuration settings for the TTA project. This module defines constants and settings used throughout the game. It's a good practice to centralize configuration to make it easier to manage and modify. Settings that might change between environments (development, production) should be loaded from environment variables.

import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# Add other configuration variables here