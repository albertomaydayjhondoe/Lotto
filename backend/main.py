"""
Main entry point for the backend application.
This imports and exposes the FastAPI app from app.main
"""
from app.main import app

__all__ = ["app"]
