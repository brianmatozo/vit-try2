# backend/scripts/export_openapi.py
import json
import sys
from pathlib import Path

# Ensure the project root is on sys.path so we can import `app`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app

# Export OpenAPI schema to dev/openapi.json
# output_path = Path(__file__).resolve().parent[2] / "openapi.json"
output_path = Path(__file__).resolve().parent / "openapi.json"

output_path.write_text(
    json.dumps(app.openapi(), indent=2),
    encoding="utf-8",
)

print(f"Wrote {output_path}")
