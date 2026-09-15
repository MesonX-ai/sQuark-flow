"""Routers package."""
# Always import costs router
from . import costs

# Try to import heavy routers (may not be available in Lambda minimal build)
try:
    from . import workflows
except ImportError:
    workflows = None

try:
    from . import executions
except ImportError:
    executions = None

try:
    from . import agents
except ImportError:
    agents = None

__all__ = ["workflows", "executions", "agents", "costs"]
