from pathlib import Path

import pytest

from assay_protocol_validator.parser import ProtocolParseError, load_yaml_file


def test_load_yaml_file_returns_mapping() -> None:
    data = load_yaml_file(Path("examples/valid_elisa.yaml"))

    assert data["assay_name"] == "cytokine_elisa"
    assert data["plate_type"] == "96_well"


def test_load_yaml_file_rejects_missing_file() -> None:
    with pytest.raises(ProtocolParseError, match="does not exist"):
        load_yaml_file("examples/does_not_exist.yaml")


def test_load_yaml_file_rejects_empty_file(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("", encoding="utf-8")

    with pytest.raises(ProtocolParseError, match="empty"):
        load_yaml_file(empty_file)
