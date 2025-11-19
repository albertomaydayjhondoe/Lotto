Clients generated / how to reproduce

Overview
- Generated outputs live inside the repository under `clients/`:
  - `clients/python` — Python client (openapi-python-client project)
  - `clients/typescript-axios` — TypeScript client (axios-based)

Regenerate the Python client (no Java required)
Run from the repository root (PowerShell):

```powershell
python -m pip install --user openapi-python-client
openapi-python-client generate --path openapi/orquestador_openapi.yaml --output-path clients/python --overwrite
```

Install/use the Python client
Option A — install the built wheel:

```powershell
cd clients/python
python -m pip install --upgrade build
python -m build
python -m pip install dist/*.whl
```

Option B — import directly in tests/apps by adding repo-relative path to PYTHONPATH:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "clients" / "python"))
from orquestador_ai_api_client import Client
```

Regenerate the TypeScript (axios) client
Option A — Docker + openapi-generator (recommended):

```powershell
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate -i /local/openapi/orquestador_openapi.yaml -g typescript-axios -o /local/clients/typescript-axios
```

Option B — JS fallback (no Java):

```powershell
npx openapi-typescript-codegen --input openapi/orquestador_openapi.yaml --output clients/typescript-axios --client axios
```

Use the TypeScript client in code:

```typescript
import { DefaultService, OpenAPI } from "../../clients/typescript-axios";
OpenAPI.BASE = "https://api.example.com";
const svc = new DefaultService();
svc.getJobs().then(console.log);
```

Committing generated code
- If you want the generated clients committed into the repo, I can add & commit them. By default generated clients are useful to keep under version control for stable contracts.

If you want me to tweak generation options (package names, versioning, templates), tell me and I will update the generation commands and re-run them.
Clients generated / how to reproduce

Python client (generated):
- Generated with `openapi-python-client` as a fallback because the local environment did not have a working Java/Docker/OpenAPI Generator setup.
- Location on the machine where generation ran: `C:\clients\python` (or `<workspace_root>/clients/python` when you run the same command in your workspace).

How to regenerate (recommended, run from repository root):
- Using openapi-python-client (no Java required):
  - python -m pip install --user openapi-python-client
  - openapi-python-client generate --path openapi/orquestador_openapi.yaml --output-path clients/python --overwrite

TypeScript (typescript-axios) client:
- I attempted to generate a TypeScript client automatically but the environment here lacked a consistent toolchain (docker daemon or Java runtime for openapi-generator). You can generate locally with one of these options:

- Option A — openapi-generator (recommended for parity with your request):
  - If you have Docker: 
    docker run --rm -v "$(pwd):/local" openapitools/openapi-generator-cli generate -i /local/openapi/orquestador_openapi.yaml -g typescript-axios -o /local/clients/typescript-axios

  - If you have Java and the openapi-generator-cli jar locally:
    java -jar openapi-generator-cli.jar generate -i openapi/orquestador_openapi.yaml -g typescript-axios -o clients/typescript-axios

- Option B — npx helper (no Java required for this tool):
  - npx openapi-typescript-codegen --input openapi/orquestador_openapi.yaml --output clients/typescript-axios --client axios

Using the Python client in your code/tests
- Install locally (recommended for CI/test):
  - cd clients/python
  - python -m pip install --upgrade build
  - python -m build
  - python -m pip install dist/<generated-wheel>.whl

- Or add the package folder to PYTHONPATH or sys.path in tests:
  - export ORQUESTADOR_PY_CLIENT_PATH="/absolute/path/to/clients/python"
  - pytest

Notes and troubleshooting
- If you want me to (a) re-run generation inside the repository workspace so outputs are committed into the repo, or (b) attempt an openapi-generator run again, say which option you prefer and I will do it next.
