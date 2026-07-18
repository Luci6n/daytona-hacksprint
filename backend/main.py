from backend.api.app import create_app
from backend.config import settings


app = create_app(settings)
