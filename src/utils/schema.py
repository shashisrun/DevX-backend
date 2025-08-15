import json
from pathlib import Path
from functools import lru_cache
from jsonschema import validate as _validate, ValidationError
from fastapi import HTTPException

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "backend" / "contracts"

@lru_cache(maxsize=None)
def _load_schema(name: str):
    path = CONTRACTS_DIR / f"{name}.schema.json"
    with path.open() as f:
        return json.load(f)


def validate_schema(data, name: str) -> None:
    schema = _load_schema(name)
    try:
        _validate(instance=data, schema=schema)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
