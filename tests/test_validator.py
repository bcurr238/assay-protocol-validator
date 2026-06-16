from assay_protocol_validator.validator import validate_protocol_data


def _valid_protocol() -> dict:
    return {
        "assay_name": "cytokine_elisa",
        "plate_type": "96_well",
        "samples": [
            {
                "id": "sample_001",
                "well": "A1",
                "volume_ul": 50,
                "donor_id": "donor_123",
            }
        ],
        "reagents": [{"name": "capture_antibody", "volume_ul": 1000}],
        "steps": [
            {
                "type": "dispense",
                "reagent": "capture_antibody",
                "destination": "all_wells",
                "volume_ul": 100,
            },
            {"type": "incubate", "duration_min": 60},
            {"type": "read_plate", "wavelength_nm": 450},
        ],
    }


def test_valid_protocol_has_no_errors() -> None:
    report = validate_protocol_data(_valid_protocol())

    assert report.is_valid
    assert report.errors == []


def test_invalid_well_is_error() -> None:
    protocol = _valid_protocol()
    protocol["samples"][0]["well"] = "Z99"

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert "not valid for plate type" in report.errors[0].message


def test_duplicate_sample_wells_are_errors() -> None:
    protocol = _valid_protocol()
    protocol["samples"].append(
        {
            "id": "sample_002",
            "well": "A1",
            "volume_ul": 50,
            "donor_id": "donor_456",
        }
    )

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert "Duplicate well" in report.errors[0].message


def test_missing_donor_id_is_error() -> None:
    protocol = _valid_protocol()
    del protocol["samples"][0]["donor_id"]

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert "samples.0.donor_id" in report.errors[0].message


def test_negative_sample_volume_is_error() -> None:
    protocol = _valid_protocol()
    protocol["samples"][0]["volume_ul"] = -1

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert "samples.0.volume_ul" in report.errors[0].message


def test_unknown_reagent_reference_is_error() -> None:
    protocol = _valid_protocol()
    protocol["steps"][0]["reagent"] = "unknown_reagent"

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert "Unknown reagent" in report.errors[0].message


def test_long_incubation_is_warning_not_error() -> None:
    protocol = _valid_protocol()
    protocol["steps"][1]["duration_min"] = 300

    report = validate_protocol_data(protocol)

    assert report.is_valid
    assert "outside the recommended range" in report.warnings[0].message


def test_unsupported_plate_type_is_error() -> None:
    protocol = _valid_protocol()
    protocol["plate_type"] = "1536_well"

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert "plate_type" in report.errors[0].message
