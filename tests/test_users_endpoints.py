from fastapi.testclient import TestClient

from app.models.users import User
from app.schemas.users import UserResponse


def _create_user_via_api(
    client: TestClient, username: str, password: str
) -> UserResponse:
    resp = client.post(
        "/api/v1/users/", json={"username": username, "password": password}
    )
    assert resp.status_code == 201
    return UserResponse.model_validate(resp.json())


class TestListUsers:
    def test_empty_database_returns_empty_list(self, client: TestClient):
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_users(self, client: TestClient):
        _create_user_via_api(client, "alice", "pw1")
        _create_user_via_api(client, "bob", "pw2")

        resp = client.get("/api/v1/users/")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["username"] == "alice"
        assert data[1]["username"] == "bob"
        assert "hashed_pass" not in data[0]
        assert "password" not in data[0]

    def test_response_never_exposes_password(self, client: TestClient):
        _create_user_via_api(client, "alice", "secret123")

        resp = client.get("/api/v1/users/")

        data = resp.json()
        assert "password" not in data[0]
        assert "hashed_pass" not in data[0]


class TestGetUser:
    def test_existing_user_returns_200(self, client: TestClient):
        created = _create_user_via_api(client, "alice", "pw")

        resp = client.get(f"/api/v1/users/{created.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == created.id
        assert data["username"] == "alice"
        assert "hashed_pass" not in data

    def test_nonexistent_user_returns_404(self, client: TestClient):
        resp = client.get("/api/v1/users/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "User not found"

    def test_zero_id_returns_404(self, client: TestClient):
        resp = client.get("/api/v1/users/0")
        assert resp.status_code == 404

    def test_negative_id_returns_404(self, client: TestClient):
        resp = client.get("/api/v1/users/-1")
        assert resp.status_code == 404

    def test_non_numeric_id_returns_422(self, client: TestClient):
        resp = client.get("/api/v1/users/abc")
        assert resp.status_code == 422


class TestCreateUser:
    def test_valid_input_returns_201(self, client: TestClient):
        resp = client.post(
            "/api/v1/users/", json={"username": "alice", "password": "secret"}
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "alice"
        assert data["id"] is not None
        assert "password" not in data
        assert "hashed_pass" not in data

    def test_missing_username_returns_422(self, client: TestClient):
        resp = client.post("/api/v1/users/", json={"password": "secret"})
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client: TestClient):
        resp = client.post("/api/v1/users/", json={"username": "alice"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client: TestClient):
        resp = client.post("/api/v1/users/", json={})
        assert resp.status_code == 422

    def test_extra_fields_are_ignored(self, client: TestClient):
        resp = client.post(
            "/api/v1/users/",
            json={"username": "alice", "password": "secret", "is_admin": True},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "is_admin" not in data

    def test_null_username_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/v1/users/", json={"username": None, "password": "secret"}
        )
        assert resp.status_code == 422

    def test_null_password_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/v1/users/", json={"username": "alice", "password": None}
        )
        assert resp.status_code == 422

    def test_empty_string_username_returns_201(self, client: TestClient):
        resp = client.post("/api/v1/users/", json={"username": "", "password": "pw"})
        assert resp.status_code == 201

    def test_empty_string_password_returns_201(self, client: TestClient):
        resp = client.post("/api/v1/users/", json={"username": "alice", "password": ""})
        assert resp.status_code == 201

    def test_integer_username_returns_422(self, client: TestClient):
        resp = client.post("/api/v1/users/", json={"username": 123, "password": "pw"})
        assert resp.status_code == 422

    def test_integer_password_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/v1/users/", json={"username": "alice", "password": 123}
        )
        assert resp.status_code == 422

    def test_idempotent_duplicate_usernames(self, client: TestClient):
        # Model has no unique constraint on username, so duplicates are allowed.
        r1 = client.post(
            "/api/v1/users/", json={"username": "alice", "password": "pw1"}
        )
        r2 = client.post(
            "/api/v1/users/", json={"username": "alice", "password": "pw2"}
        )
        assert r1.status_code == 201
        assert r2.status_code == 201


class TestDeleteUser:
    def test_existing_user_returns_204(self, client: TestClient):
        created = _create_user_via_api(client, "alice", "pw")

        resp = client.delete(f"/api/v1/users/{created.id}")

        assert resp.status_code == 204
        assert resp.text == ""

        # Verify it's actually gone.
        get_resp = client.get(f"/api/v1/users/{created.id}")
        assert get_resp.status_code == 404

    def test_nonexistent_user_returns_404(self, client: TestClient):
        resp = client.delete("/api/v1/users/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "User not found"

    def test_zero_id_returns_404(self, client: TestClient):
        resp = client.delete("/api/v1/users/0")
        assert resp.status_code == 404

    def test_negative_id_returns_404(self, client: TestClient):
        resp = client.delete("/api/v1/users/-1")
        assert resp.status_code == 404

    def test_non_numeric_id_returns_422(self, client: TestClient):
        resp = client.delete("/api/v1/users/abc")
        assert resp.status_code == 422

    def test_double_delete_returns_404_on_second(self, client: TestClient):
        created = _create_user_via_api(client, "alice", "pw")

        r1 = client.delete(f"/api/v1/users/{created.id}")
        assert r1.status_code == 204

        r2 = client.delete(f"/api/v1/users/{created.id}")
        assert r2.status_code == 404
