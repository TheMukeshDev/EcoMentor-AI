"""EcoMentor AI backend entrypoint.

Loads environment variables and creates the Flask application
using the app factory pattern.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app

config_name: str = os.getenv("APP_ENV", "development")
app = create_app(config_name)
