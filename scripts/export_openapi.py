"""
Экспортирует OpenAPI-спецификацию из FastAPI-приложения.

Использование:
    python -m scripts.export_openapi              # → openapi.json
    python -m scripts.export_openapi --yaml       # → openapi.yaml
    python -m scripts.export_openapi --out spec   # → spec.json

Полезно для сравнения автогенерированной спецификации с контрактом (openapi.yaml),
чтобы отловить дрифт.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export OpenAPI spec from FastAPI app")
    parser.add_argument("--yaml", action="store_true", help="Output as YAML instead of JSON")
    parser.add_argument("--out", type=str, default="openapi", help="Output filename (without extension)")
    args = parser.parse_args()

    from backend.main import app

    spec = app.openapi()

    if args.yaml:
        try:
            import yaml
        except ImportError:
            print("pip install pyyaml to export as YAML", file=sys.stderr)
            sys.exit(1)
        out_path = ROOT / f"{args.out}.yaml"
        out_path.write_text(yaml.dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    else:
        out_path = ROOT / f"{args.out}.json"
        out_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Exported to {out_path}")


if __name__ == "__main__":
    main()
