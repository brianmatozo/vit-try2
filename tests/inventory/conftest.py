from fastapi.testclient import TestClient


def create_test_product(client: TestClient, **kwargs) -> int:
    payload = {
        "sku": "NUT-CASHEW",
        "name": "Castañas de Cajú",
        "unit_price": 2500,  # $2,500 whole ARS per 100g
        "bulk_reference_grams": 100,
        "plu_code": "0175",
        "product_type": "bulk",
        "current_stock": 0,
        "min_safety_buffer": 500,
    }
    payload.update(kwargs)
    resp = client.post("/api/v1/products", json=payload)
    assert resp.status_code == 200
    prod_id = client.get("/api/v1/products").json()["data"][-1]["id"]
    return prod_id
