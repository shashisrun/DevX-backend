import os
import sys
import asyncio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test.db")

from src.models import project  # ensure models are registered
from src.db import init_db

# Ensure database tables exist before tests run
asyncio.run(init_db())
