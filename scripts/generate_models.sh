#!/usr/bin/env bash
# Генерация Pydantic-моделей из OpenAPI-контракта.
#
# Использование:
#   ./scripts/generate_models.sh
#
# Требования:
#   pip install datamodel-code-generator
#
# Результат:
#   generated/models.py — строго типизированные Pydantic-модели,
#   сгенерированные из openapi.yaml (source of truth).
#   Используйте для валидации совместимости ваших схем с контрактом.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT="$PROJECT_ROOT/openapi.yaml"
OUTPUT="$PROJECT_ROOT/generated/models.py"

if ! command -v datamodel-codegen &>/dev/null; then
    echo "ERROR: datamodel-codegen not found. Install: pip install datamodel-code-generator"
    exit 1
fi

echo "Generating Pydantic models from $INPUT..."
datamodel-codegen \
    --input "$INPUT" \
    --input-file-type openapi \
    --output "$OUTPUT" \
    --output-model-type pydantic_v2.BaseModel \
    --use-standard-collections \
    --use-union-operator \
    --target-python-version 3.11 \
    --field-constraints \
    --enum-field-as-literal all

echo "Models generated: $OUTPUT"
echo ""
echo "To validate your existing schemas match the contract, run:"
echo "  python -c \"from generated.models import *; print('OK')\""
