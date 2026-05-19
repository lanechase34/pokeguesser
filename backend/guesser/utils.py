import json
from pathlib import Path

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

SCHEMA_DIR = Path(__file__).parent / "schemas"


def load_schema(filename: str) -> dict:
    path = SCHEMA_DIR / filename
    with open(path) as f:
        data = json.load(f)

    # Resolve any $refs to local files
    data = _resolve_refs(data, path.parent)
    return data


def _resolve_refs(schema: dict, base_dir: Path) -> dict:
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_path = (base_dir / schema["$ref"]).resolve()
            with open(ref_path) as f:
                return _resolve_refs(json.load(f), ref_path.parent)
        return {k: _resolve_refs(v, base_dir) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_resolve_refs(i, base_dir) for i in schema]
    return schema


error_response = inline_serializer(
    name="ErrorResponse", fields={"error": serializers.CharField()}
)
