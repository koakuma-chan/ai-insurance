"""Configuration settings for the car insurance telegram bot.

This module loads environment variables and provides configuration settings
for the entire application. It validates critical settings and ensures
the data directory exists.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    logger.error("Error: 'BOT_TOKEN' is not set.")
    sys.exit(1)

# OpenAI API configuration
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    logger.error("Error: 'OPENAI_API_KEY' is not set.")
    sys.exit(1)

# Mindee API configuration
MINDEE_API_KEY: str = os.getenv("MINDEE_API_KEY", "")
if not MINDEE_API_KEY:
    logger.error("Error: 'MINDEE_API_KEY' is not set.")
    sys.exit(1)

MINDEE_ACCOUNT_NAME: str = os.getenv("MINDEE_ACCOUNT_NAME", "")
if not MINDEE_ACCOUNT_NAME:
    logger.error("Error: 'MINDEE_ACCOUNT_NAME' is not set.")
    sys.exit(1)

# Data directory configuration
DATA_DIRECTORY_PATH: str = os.getenv("DATA_DIRECTORY_PATH", "./data")
data_dir = Path(DATA_DIRECTORY_PATH)
try:
    data_dir.mkdir(parents=True, exist_ok=True)
except PermissionError:
    logger.error(
        f"Error: No permission to create data directory at {DATA_DIRECTORY_PATH}"
    )
    sys.exit(1)

# Agent model configuration
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4.1-nano-2025-04-14")

# Timeout configuration (seconds)
MEDIA_GROUP_TIMEOUT: float = float(os.getenv("MEDIA_GROUP_TIMEOUT", "2.0"))

# Database configuration
DATABASE_FILENAME: str = os.getenv("DATABASE_FILENAME", "db.sqlite")
DATABASE_PATH: str = os.path.join(DATA_DIRECTORY_PATH, DATABASE_FILENAME)

# Max conversation history messages
MAX_MESSAGES: int = int(os.getenv("MAX_MESSAGES", "64"))

# AI Agent names - make them configurable
AGENT_NAMES: Dict[str, str] = {
    "hub": "hub_agent",
    "document_processor": "document_processor_agent",
    "price_negotiator": "price_negotiator_agent",
    "insurance_policy": "insurance_policy_agent",
}
