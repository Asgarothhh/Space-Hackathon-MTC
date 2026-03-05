#!/usr/bin/env bash
# Генерация TypeScript API-клиента из OpenAPI-контракта.
#
# Использование:
#   ./scripts/generate_client.sh
#
# Требования:
#   npx (Node.js)
#
# Результат:
#   generated/api-client/ — типизированный TypeScript-клиент
#   Фронтенд больше не пишет ручные fetch-запросы.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT="$PROJECT_ROOT/openapi.yaml"
OUTPUT_DIR="$PROJECT_ROOT/generated/api-client"

mkdir -p "$OUTPUT_DIR"

echo "Generating TypeScript API client from $INPUT..."

npx @hey-api/openapi-ts \
    -i "$INPUT" \
    -o "$OUTPUT_DIR" \
    -c @hey-api/client-fetch

echo ""
echo "TypeScript API client generated: $OUTPUT_DIR"
echo ""
echo "Usage in frontend:"
echo '  import { createVM, getVM, startVM } from "./generated/api-client";'
echo ""
echo '  const vm = await createVM({ body: { name: "my-vm", cpu: 2, ram: 4096, ssd: 50 } });'
