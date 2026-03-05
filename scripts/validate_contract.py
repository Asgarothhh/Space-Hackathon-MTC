"""
Сравнивает OpenAPI-контракт (openapi.yaml) с автогенерированной спецификацией FastAPI.

Обнаруживает дрифт: когда бэкенд и контракт разошлись.

Использование:
    python -m scripts.validate_contract
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _flatten_paths(spec: dict) -> set[str]:
    result = set()
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            if method in ("get", "post", "put", "patch", "delete", "head", "options"):
                result.add(f"{method.upper()} {path}")
    return result


def _flatten_schemas(spec: dict) -> set[str]:
    return set(spec.get("components", {}).get("schemas", {}).keys())


def main() -> None:
    import yaml

    contract_path = ROOT / "openapi.yaml"
    if not contract_path.exists():
        print("ERROR: openapi.yaml not found", file=sys.stderr)
        sys.exit(1)

    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))

    from backend.main import app
    fastapi_spec = app.openapi()

    contract_paths = _flatten_paths(contract)
    fastapi_paths = _flatten_paths(fastapi_spec)

    contract_schemas = _flatten_schemas(contract)
    fastapi_schemas = _flatten_schemas(fastapi_spec)

    issues = []

    missing_in_backend = contract_paths - fastapi_paths
    if missing_in_backend:
        issues.append(f"Endpoints in contract but NOT in backend:\n" +
                       "\n".join(f"  - {p}" for p in sorted(missing_in_backend)))

    missing_in_contract = fastapi_paths - contract_paths
    if missing_in_contract:
        issues.append(f"Endpoints in backend but NOT in contract:\n" +
                       "\n".join(f"  - {p}" for p in sorted(missing_in_contract)))

    missing_schemas_contract = contract_schemas - fastapi_schemas
    if missing_schemas_contract:
        issues.append(f"Schemas in contract but NOT in backend:\n" +
                       "\n".join(f"  - {s}" for s in sorted(missing_schemas_contract)))

    if issues:
        print("DRIFT DETECTED between openapi.yaml and FastAPI app:\n")
        for issue in issues:
            print(issue)
            print()
        sys.exit(1)
    else:
        print("OK — no drift detected between openapi.yaml and FastAPI app")
        print(f"  Endpoints: {len(contract_paths)} in contract, {len(fastapi_paths)} in backend")
        print(f"  Schemas:   {len(contract_schemas)} in contract, {len(fastapi_schemas)} in backend")


if __name__ == "__main__":
    main()
