from pathlib import Path

# POC test: import the Python client and check TypeScript file exists.
# NOTE: This file is not executed automatically here; user will run pytest manually.

# The test below imports the generated Python client package and checks the
# presence of the TypeScript index file. We add clients/python to sys.path so
# the generated package (inside that directory) can be imported.
import importlib
import sys
from pathlib import Path

# Ensure the generated Python client folder is on sys.path so imports resolve.
repo_root = Path(__file__).resolve().parent.parent
py_client_path = repo_root / "clients" / "python"
sys.path.insert(0, str(py_client_path))


def test_poc_clients_import_and_ts_exists():
    # Try importing the generated Python package (support two possible names).
    orq = None
    for pkg in ("orquestador_api_client", "orquestador_ai_api_client"):
        try:
            orq = importlib.import_module(pkg)
            break
        except Exception:
            continue
    assert orq is not None, (
        "Could not import local Python client package; expected 'orquestador_api_client' or 'orquestador_ai_api_client'."
    )

    # Verify a TypeScript client file exists (common output path for the generator)
    ts_index_paths = [
        repo_root / "clients" / "typescript" / "src" / "index.ts",
        repo_root / "clients" / "typescript" / "index.ts",
    ]

    assert any(p.exists() for p in ts_index_paths), "TypeScript client index file not found under clients/typescript."
