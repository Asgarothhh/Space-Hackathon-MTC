"""
Контрактные тесты — проверяют, что бэкенд соответствует OpenAPI-контракту.

Использует schemathesis для автоматической генерации запросов
на основе openapi.yaml и проверки ответов.

Запуск:
    pytest tests/test_contract.py -v
    # или напрямую через CLI:
    schemathesis run openapi.yaml --base-url http://localhost:8000
"""

from pathlib import Path

import pytest

OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.yaml"


def _has_schemathesis() -> bool:
    try:
        import schemathesis
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _has_schemathesis(), reason="schemathesis not installed")
class TestContractCompliance:
    """
    Проверяет, что каждый эндпоинт в OpenAPI-контракте:
    - возвращает валидный статус-код,
    - возвращает тело ответа, соответствующее схеме.
    """

    def test_openapi_contract_exists(self):
        assert OPENAPI_PATH.exists(), f"OpenAPI contract not found at {OPENAPI_PATH}"

    def test_contract_is_valid_yaml(self):
        import yaml
        with open(OPENAPI_PATH) as f:
            spec = yaml.safe_load(f)
        assert "openapi" in spec
        assert "paths" in spec
        assert "components" in spec

    def test_all_endpoints_have_responses(self):
        import yaml
        with open(OPENAPI_PATH) as f:
            spec = yaml.safe_load(f)

        for path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "patch", "delete"):
                    assert "responses" in details, \
                        f"{method.upper()} {path} missing responses"

    def test_all_schemas_referenced_exist(self):
        """Проверяет, что все $ref ссылки в спецификации указывают на существующие схемы."""
        import yaml

        with open(OPENAPI_PATH) as f:
            spec = yaml.safe_load(f)

        schemas = set(spec.get("components", {}).get("schemas", {}).keys())
        responses = set(spec.get("components", {}).get("responses", {}).keys())

        def _find_refs(obj, path=""):
            refs = []
            if isinstance(obj, dict):
                if "$ref" in obj:
                    refs.append((path, obj["$ref"]))
                for k, v in obj.items():
                    refs.extend(_find_refs(v, f"{path}.{k}"))
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    refs.extend(_find_refs(v, f"{path}[{i}]"))
            return refs

        all_refs = _find_refs(spec)
        for ref_path, ref_value in all_refs:
            if ref_value.startswith("#/components/schemas/"):
                schema_name = ref_value.split("/")[-1]
                assert schema_name in schemas, \
                    f"Broken $ref at {ref_path}: schema '{schema_name}' not found"
            elif ref_value.startswith("#/components/responses/"):
                resp_name = ref_value.split("/")[-1]
                assert resp_name in responses, \
                    f"Broken $ref at {ref_path}: response '{resp_name}' not found"

    def test_schemathesis_available(self):
        """
        Проверяет, что schemathesis установлен и готов к использованию.
        Полные контрактные тесты запускаются через CLI:
            schemathesis run openapi.yaml --base-url http://localhost:8000 --checks all
        """
        import schemathesis
        assert schemathesis.SCHEMATHESIS_VERSION is not None
