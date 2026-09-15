"""AWS Lambda entry point for unified backend."""
# Workaround for missing botocore.docs in Lambda environment
import sys
from types import ModuleType

# Create dummy modules for botocore.docs
sys.modules['botocore.docs'] = ModuleType('botocore.docs')
sys.modules['botocore.docs.docstring'] = ModuleType('botocore.docs.docstring')
sys.modules['botocore.docs.utils'] = ModuleType('botocore.docs.utils')

from mangum import Mangum
from app.main import app

# Wrap FastAPI app with Mangum ASGI adapter for Lambda
handler = Mangum(app, lifespan="auto")
