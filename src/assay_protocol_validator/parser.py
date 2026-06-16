"""File parsing helpers for assay protocol files."""

from pathlib import Path
from typing import Any

import yaml


class ProtocolParseError(Exception):
    """Raised when a protocol file cannot be loaded as structured YAML."""


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    """Load a YAML protocol file into a dictionary."""

    protocol_path = Path(path)
    if not protocol_path.exists():
        raise ProtocolParseError(f"Protocol file does not exist: {protocol_path}")

    try:
        with protocol_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ProtocolParseError(f"Could not parse YAML: {exc}") from exc

    if data is None:
        raise ProtocolParseError("Protocol file is empty.")

    if not isinstance(data, dict):
        raise ProtocolParseError("Protocol file must contain a YAML mapping at the top level.")

    return data
