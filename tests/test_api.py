"""Exercise validation through the HTTP interface."""

from fastapi.testclient import TestClient

from assay_protocol_validator.api import app
from assay_protocol_validator.parser import load_yaml_file
from assay_protocol_validator.validator import validate_protocol_data


client = TestClient(app)


def test_unknown_reagent_returns_422():
    protocol = load_yaml_file("examples/evaluation/pcr_setup_unknown_reagent.yaml")

    response = client.post("/validate", json=protocol)

    assert response.status_code == 422
    report = response.json()
    assert report["status"] == "invalid"
    assert report["errors"][0]["code"] == "UNKNOWN_REAGENT"
    assert report == validate_protocol_data(protocol).to_dict()


def test_missing_metadata_returns_422():
    protocol = load_yaml_file("examples/evaluation/dsdna_missing_sample_metadata.yaml")

    response = client.post("/validate", json=protocol)

    assert response.status_code == 422
    report = response.json()
    assert report["status"] == "invalid"
    assert report["errors"][0]["code"] == "SCHEMA_VALIDATION_ERROR"
    assert report == validate_protocol_data(protocol).to_dict()


def test_warning_only_protocol_returns_200():
    protocol = load_yaml_file("examples/evaluation/viability_long_incubation.yaml")

    response = client.post("/validate", json=protocol)

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "valid"
    assert report["errors"] == []
    assert report["warnings"][0]["code"] == "UNUSUAL_INCUBATION_DURATION"
    assert report == validate_protocol_data(protocol).to_dict()


def test_valid_protocol_returns_200():
    protocol = load_yaml_file("examples/evaluation/viability_plate_baseline.yaml")

    response = client.post("/validate", json=protocol)

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "valid"
    assert report["errors"] == []
    assert report["warnings"] == []
    assert report == validate_protocol_data(protocol).to_dict()
