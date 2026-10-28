import pytest

from server.modules.remitos.client import encode_image_bytes, extract_remito
from server.modules.remitos.schemas import RemitoVisionOutput


def test_schema_validation_against_all_fixtures(load_remito_fixture):
    for filename in [
        "natural_output.json",
        "new_day_output.json",
        "vivet_output.json",
    ]:
        data = load_remito_fixture(filename)
        output = RemitoVisionOutput.model_validate(data)
        assert output.supplier_name != ""
        assert len(output.items) > 0
        for item in output.items:
            assert item.line_index >= 0
            assert item.raw_description != ""
            assert item.unit_cost >= 0


@pytest.mark.anyio
async def test_extract_remito_mock_mode(load_remito_fixture):
    data = load_remito_fixture("new_day_output.json")
    mock_obj = RemitoVisionOutput.model_validate(data)

    # Calling extract_remito with mock_response executes zero network calls
    res = await extract_remito(["data:image/jpeg;base64,AAAA"], mock_response=mock_obj)
    assert res.supplier_name == "New Day"
    assert len(res.items) == 46


def test_encode_image_bytes():
    raw = b"vitalcer-receipt-test-bytes"
    uri = encode_image_bytes(raw, mime_type="image/jpeg")
    assert uri.startswith("data:image/jpeg;base64,")
