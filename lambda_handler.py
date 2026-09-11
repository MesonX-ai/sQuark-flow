"""AWS Lambda entry point for unified backend."""
from mangum import Mangum
from app.main import app

# Wrap FastAPI app with Mangum ASGI adapter for Lambda
handler = Mangum(app, lifespan="auto")
