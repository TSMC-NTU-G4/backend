from fastapi.testclient import TestClient

from app.models.response import Response as APIResponse


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200

    parsed = APIResponse(**response.json())
    assert parsed.message == "Welcome to the Earthquake API!"
    assert parsed.data is None
