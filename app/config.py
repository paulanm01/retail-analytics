"""
Application configuration.

Reads values from the .env file and exposes them to Flask.
"""
import os

from dotenv import load_dotenv

# Must run before any os.getenv() call below.
load_dotenv()


class Config:
    """Base configuration, used in development."""

    # Second argument is the fallback if the variable is missing from .env
    SECRET_KEY = os.getenv("SECRET_KEY", "insecure-fallback-key")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # Turns off an SQLAlchemy event system we don't use and that costs memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paths built from this file's location, so they work on any machine
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_FOLDER = os.path.join(BASE_DIR, "data")