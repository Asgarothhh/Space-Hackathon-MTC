"""
Тесты health-check и root endpoints.
"""


class TestRoot:
    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "status" in resp.json()
