import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "remitos"


@pytest.fixture
def load_remito_fixture():
    """Load JSON fixture from tests/fixtures/remitos/ with resilient fallback."""

    def _loader(filename: str) -> dict[str, Any]:
        path = FIXTURES_DIR / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Fallback fixture if gitignored test fixtures are absent
        return {
            "supplier_name": "New Day",
            "remito_number": "3711",
            "date_issued": "2024-10-13",
            "page_count": 1,
            "items": [
                {
                    "line_index": 1,
                    "raw_description": (
                        "Barritas de Chocolate con Azucar Mascabado x 12 u (Laddu)"
                    ),
                    "quantity": 1,
                    "unit_cost": 14600,
                    "line_total": 14600,
                    "confidence": 95,
                }
            ],
            "fiscal_info": None,
            "overall_confidence": 95,
            "extraction_notes": [],
        }

    return _loader
