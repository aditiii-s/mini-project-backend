"""Vercel serverless entry point.

Vercel's Python runtime looks for an ASGI application named `app` in this file.
All routes are rewritten here by vercel.json, so FastAPI still sees the original
path (for example /api/auth/login).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

__all__ = ["app"]
