"""
Exports the active FastAPI application OpenAPI schema to JSON.
"""

import json
import os
import sys

# Ensure src is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))

try:
    from plagiarism.main import app

    openapi_schema = app.openapi()
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contracts", "generated"))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "openapi.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"Successfully exported OpenAPI schema to: {output_file}")
except Exception as e:
    print(f"Could not export schema (dependencies may not be installed): {e}")
