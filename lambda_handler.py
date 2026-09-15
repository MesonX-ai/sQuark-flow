"""AWS Lambda entry point for unified backend."""
# Workaround for missing botocore.docs in Lambda environment
import sys
from types import ModuleType

# Create dummy modules and classes for botocore.docs
botocore_docs = ModuleType('botocore.docs')
botocore_docs_docstring = ModuleType('botocore.docs.docstring')
botocore_docs_utils = ModuleType('botocore.docs.utils')

# Add empty classes that boto3 might try to import
class DocstringDocumenter:
    pass

class ClientMethodDocstring(DocstringDocumenter):
    pass

class PaginatorDocstring(DocstringDocumenter):
    pass

class WaiterDocstring(DocstringDocumenter):
    pass

# Attach classes to modules
botocore_docs_docstring.DocstringDocumenter = DocstringDocumenter
botocore_docs_docstring.ClientMethodDocstring = ClientMethodDocstring
botocore_docs_docstring.PaginatorDocstring = PaginatorDocstring
botocore_docs_docstring.WaiterDocstring = WaiterDocstring
botocore_docs_docstring.LazyLoadedDocstring = DocstringDocumenter

# Register modules
sys.modules['botocore.docs'] = botocore_docs
sys.modules['botocore.docs.docstring'] = botocore_docs_docstring
sys.modules['botocore.docs.utils'] = botocore_docs_utils

from mangum import Mangum
from app.main import app

# Wrap FastAPI app with Mangum ASGI adapter for Lambda
handler = Mangum(app, lifespan="auto")
