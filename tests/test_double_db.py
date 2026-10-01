from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from sqlmodel import Session, select

from server.core.db import get_async_database_url, get_sync_database_url
from server.models.products import Product, ProductType
from server.models.users import User


class TestDatabaseURLTranslation:
    def test_sync_url_normalization(self):
        assert (
            get_sync_database_url("sqlite+aiosqlite:///test.db") == "sqlite:///test.db"
        )
        assert (
            get_sync_database_url("postgres://u:p@host:5432/db")
            == "postgresql+psycopg://u:p@host:5432/db"
        )
        assert (
            get_sync_database_url("postgresql://u:p@host:5432/db")
            == "postgresql+psycopg://u:p@host:5432/db"
        )
        assert (
            get_sync_database_url("postgresql+psycopg://u:p@host:5432/db")
            == "postgresql+psycopg://u:p@host:5432/db"
        )

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


class TestDoubleDBSynchronization:
    def test_sync_write_async_read(self, db_session: Session, client: TestClient):
        """Record written via sync session is immediately readable via async."""
        prod = Product(
            sku="SYNC-TO-ASYNC",
            name="Sync Written Product",
            unit_price=1200,
            product_type=ProductType.DISCRETE,
            current_stock=100,
        )
        db_session.add(prod)
        db_session.commit()
        prod_id = prod.id

        # Read via async FastCRUD endpoint
        resp = client.get(f"/api/v1/products/{prod_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sku"] == "SYNC-TO-ASYNC"
        assert data["current_stock"] == 100

    def test_async_write_sync_read(self, db_session: Session, client: TestClient):
        """Record created via async endpoint is readable via sync session."""
        resp = client.post(
            "/api/v1/products",
            json={
                "sku": "ASYNC-TO-SYNC",
                "name": "Async Written Product",
                "unit_price": 3000,
                "current_stock": 250,
            },
        )
        assert resp.status_code == 200

        db_session.expire_all()
        stmt = select(Product).where(Product.sku == "ASYNC-TO-SYNC")
        product = db_session.scalars(stmt).first()
        assert product is not None
        assert product.unit_price == 3000
        assert product.current_stock == 250

    def test_sync_users_and_async_products_coexist(self, client: TestClient):
        """Sync endpoints (users) and async endpoints (products) share DB."""
        # 1. Create user via sync endpoint
        u_resp = client.post(
            "/api/v1/users/",
            json={"username": "dual_admin", "password": "securepassword123"},
        )
        assert u_resp.status_code == 201
        user_id = u_resp.json()["id"]

        # 2. Create product via async endpoint
        p_resp = client.post(
            "/api/v1/products",
            json={"sku": "DUAL-ITEM", "name": "Dual Item", "unit_price": 500},
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
