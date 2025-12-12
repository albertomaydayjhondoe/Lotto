from pathlib import Path


def test_typescript_client_files_exist():
    repo_root = Path(__file__).resolve().parents[1]
    ts_client = repo_root / "clients" / "typescript-axios"
    assert ts_client.exists(), f"TypeScript client directory not found at {ts_client}"
    assert (ts_client / "index.ts").exists() or (ts_client / "index.js").exists(), "index file missing in TypeScript client"
    assert (ts_client / "services").exists(), "services folder missing in TypeScript client"
