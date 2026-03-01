"""Shared Annotated types for use in FastAPI path / query parameters."""
from typing import Annotated

from fastapi import Path

# Matches any standard UUID (v1–v5, case-insensitive)
_UUID_RE = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

UUIDPath = Annotated[str, Path(pattern=_UUID_RE, description="UUID identifier")]
