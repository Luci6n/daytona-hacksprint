from pathlib import Path
import sys


if __package__ in {None, ""}:
    # Support the AGENTS.md command: cd backend; uvicorn main:app
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api.app import create_app
from backend.config import settings


app = create_app(settings)
