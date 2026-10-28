from fastapi.testclient import TestClient


def test_remitos_api_lifecycle(client: TestClient):
    # 1. Create a product first
    p_resp = client.post(
        "/api/v1/products",
        json={
            "sku": "ALF-LADDU-TEST",
            "name": "Alfajor Laddu Test",
            "unit_price": 2500,
            "product_type": "discrete",
        },
    )
    assert p_resp.status_code == 200
    prod_id = p_resp.json()["id"]

    # 2. Stage a Remito
    stage_payload = {
        "supplier_name": "New Day Test",
        "remito_number": "R-9999",
        "date_issued": "2024-10-15",
        "items": [
            {
                "line_index": 0,
                "raw_description": "Alfajor Laddu Test x 10 u",
                "quantity": 3,
                "unit_cost": 8000,
                "line_total": 24000,
                "confidence": 95,
            }
        ],
    }
    s_resp = client.post(
        "/api/v1/remitos/scan-and-stage?blanco_pct=60&negro_pct=40&iva_pct=21",
        json=stage_payload,
    )
    assert s_resp.status_code == 201
    remito_data = s_resp.json()
    remito_id = remito_data["id"]
    item_id = remito_data["items"][0]["id"]
    assert remito_data["status"] == "staged"

    # 3. List Remitos
    list_resp = client.get("/api/v1/remitos?status=staged")
    assert list_resp.status_code == 200
    assert any(r["id"] == remito_id for r in list_resp.json())

    # 4. Get single Remito
    get_resp = client.get(f"/api/v1/remitos/{remito_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["supplier_name"] == "New Day Test"

    # 5. Inline edit item
    put_resp = client.put(
        f"/api/v1/remitos/{remito_id}/items/{item_id}",
        json={"product_id": prod_id, "effective_quantity": 3},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["product_id"] == prod_id
    assert put_resp.json()["quantity_to_commit"] == 30

    # 6. Confirm Remito
    conf_resp = client.post(f"/api/v1/remitos/{remito_id}/confirm")
    assert conf_resp.status_code == 200
    assert conf_resp.json()["status"] == "committed"

    # Verify product stock updated via products endpoint
    prod_check = client.get(f"/api/v1/products/{prod_id}").json()
    assert prod_check["current_stock"] == 30
    assert prod_check["last_cost"] > 0

    # 7. Check Supplier Mappings Dictionary
    m_resp = client.get("/api/v1/supplier-mappings?supplier=New Day")
    assert m_resp.status_code == 200
    mappings = m_resp.json()
    assert len(mappings) >= 1
    mapping_id = mappings[0]["id"]

    # 8. Delete Supplier Mapping
    del_resp = client.delete(f"/api/v1/supplier-mappings/{mapping_id}")
    assert del_resp.status_code == 204


def test_get_nonexistent_remito_404(client: TestClient):
    resp = client.get("/api/v1/remitos/999999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_remito_config_and_scan_images(client: TestClient):
    # Test config GET and POST
    c_resp = client.get("/api/v1/remitos/config")
    assert c_resp.status_code == 200
    assert "has_api_key" in c_resp.json()

    up_resp = client.post(
        "/api/v1/remitos/config",
        json={"primary_model": "google/gemini-2.0-flash-001"},
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["primary_model"] == "google/gemini-2.0-flash-001"

    # Test scan-images in mock mode
    s_resp = client.post(
        "/api/v1/remitos/scan-images",
        json={"mock": True, "images": ["data:image/jpeg;base64,123"]},
    )
    assert s_resp.status_code == 201
    remito = s_resp.json()
    assert remito["status"] == "staged"

    # Test patch header fiscal split
    p_resp = client.patch(
        f"/api/v1/remitos/{remito['id']}",
        json={"fiscal_blanco_pct": 50, "fiscal_negro_pct": 50},
    )
    assert p_resp.status_code == 200
    assert p_resp.json()["fiscal_blanco_bps"] == 5000
