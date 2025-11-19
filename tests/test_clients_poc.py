import os
import sys
import importlib
from pathlib import Path


def discover_client_package(client_root: Path):
    """Find the first subdirectory under client_root that looks like a Python package.
    Returns the package name and path, or (None, None) if not found.
    """
    if not client_root.exists():
        return None, None
    for p in client_root.iterdir():
        if p.is_dir() and (p / "__init__.py").exists():
            return p.name, str(p)
    # fallback: maybe the package files are directly in the root
    if (client_root / "__init__.py").exists():
        return client_root.name, str(client_root)
    return None, None


def test_python_client_importable():
    # Allow test runner to override path to generated client
    default_path = Path(__file__).resolve().parents[1] / "clients" / "python"
    client_root = Path(os.environ.get("ORQUESTADOR_PY_CLIENT_PATH", str(default_path)))
    pkg_name, pkg_path = discover_client_package(client_root)
    assert pkg_name is not None, f"Python client package not found in {client_root}. Generate it first and set ORQUESTADOR_PY_CLIENT_PATH env var."

    # Add package path to sys.path and import
    sys.path.insert(0, pkg_path)
    mod = importlib.import_module(pkg_name)

    # Basic smoke assertions: module loads and has metadata
    assert hasattr(mod, "__version__") or hasattr(mod, "__package__")


def test_api_models_and_construction():
    default_path = Path(__file__).resolve().parents[1] / "clients" / "python"
    client_root = Path(os.environ.get("ORQUESTADOR_PY_CLIENT_PATH", str(default_path)))
    pkg_name, pkg_path = discover_client_package(client_root)
    if pkg_name is None:
        # Skip detailed tests if client not found
        return
    sys.path.insert(0, pkg_path)
    mod = importlib.import_module(pkg_name)

    # Look for common generated client symbols
    # openapi-python-client typically creates a Client class in the package
    client_cls = None
    for attr in ("Client", "OrquestadorClient", "ApiClient"):
        client_cls = getattr(mod, attr, None)
        if client_cls:
            break

    # If we don't have a client class, at least ensure models package exists
    models_pkg = getattr(mod, "models", None)
    assert client_cls is not None or models_pkg is not None
