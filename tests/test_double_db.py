from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from server.core.db import get_async_database_url
from server.models.products import Product
from server.models.users import User


class TestDatabaseURLTranslation:
    def test_async_url_translation(self):
        assert (
            get_async_database_url("sqlite:///test.db") == "sqlite+aiosqlite:///test.db"
        )
        assert (
            get_async_database_url("postgres://u:p@host:5432/db")
            == "postgresql+psycopg://u:p@host:5432/db"
        )
        assert (
            get_async_database_url("postgresql://u:p@host:5432/db")
            == "postgresql+psycopg://u:p@host:5432/db"
        )
        assert (
            get_async_database_url("postgresql+psycopg://u:p@host:5432/db")
            == "postgresql+psycopg://u:p@host:5432/db"
        )


class TestStandardizedDBOperations:
    def test_users_and_products_endpoints_coexist(self, client: TestClient):
        """Async users endpoints and async products endpoints operate seamlessly."""
        # 1. Create user via async endpoint
        u_resp = client.post(
            "/api/v1/users/",
            json={"username": "async_admin", "password": "securepassword123"},
        )
        assert u_resp.status_code == 201
        user_id = u_resp.json()["id"]

        # 2. Create product via async endpoint
        p_resp = client.post(
            "/api/v1/products",
            json={"sku": "ASYNC-ITEM", "name": "Async Item", "unit_price": 500},
        )
        assert p_resp.status_code == 200

        # 3. Read both back
        assert client.get(f"/api/v1/users/{user_id}").status_code == 200
        assert client.get("/api/v1/products").status_code == 200


class TestPostgresCompatibility:
    def test_postgres_ddl_generation(self):
        """Ensure all SQLModel models produce valid PostgreSQL DDL without errors."""
        dialect = postgresql.dialect()
        user_ddl = str(
            CreateTable(User.metadata.tables["users"]).compile(dialect=dialect)
        )
        product_ddl = str(
            CreateTable(Product.metadata.tables["products"]).compile(dialect=dialect)
        )

        assert "CREATE TABLE users" in user_ddl
        assert "SERIAL" in user_ddl

        assert "CREATE TABLE products" in product_ddl
        assert "SERIAL" in product_ddl
        assert "unit_price INTEGER" in product_ddl
        assert "bulk_reference_grams INTEGER" in product_ddl
