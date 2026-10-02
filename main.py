"""
Root entrypoint for Render and production deployments.
Enables running `uvicorn main:app` directly from the repository root.
"""
import importlib.util
import sys
from pathlib import Path

# Add backend directory to sys.path so submodules (from models import ..., etc.) resolve cleanly
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load backend/main.py module directly to avoid circular self-import of root main.py
spec = importlib.util.spec_from_file_location("backend_main", str(BACKEND_DIR / "main.py"))
backend_main = importlib.util.module_from_spec(spec)
sys.modules["backend_main"] = backend_main
spec.loader.exec_module(backend_main)

app = backend_main.app
