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
    assert report.errors[0].code == "INVALID_WELL"
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
    assert report.errors[0].code == "DUPLICATE_SAMPLE_WELL"
    assert "Duplicate well" in report.errors[0].message


def test_missing_donor_id_is_error() -> None:
    protocol = _valid_protocol()
    del protocol["samples"][0]["donor_id"]

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert report.errors[0].code == "SCHEMA_VALIDATION_ERROR"
    assert "samples.0.donor_id" in report.errors[0].message


def test_negative_sample_volume_is_error() -> None:
    protocol = _valid_protocol()
    protocol["samples"][0]["volume_ul"] = -1

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert report.errors[0].code == "SCHEMA_VALIDATION_ERROR"
    assert "samples.0.volume_ul" in report.errors[0].message


def test_unknown_reagent_reference_is_error() -> None:
    protocol = _valid_protocol()
    protocol["steps"][0]["reagent"] = "unknown_reagent"

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert report.errors[0].code == "UNKNOWN_REAGENT"
    assert "Unknown reagent" in report.errors[0].message


def test_long_incubation_is_warning_not_error() -> None:
    protocol = _valid_protocol()
    protocol["steps"][1]["duration_min"] = 300

    report = validate_protocol_data(protocol)

    assert report.is_valid
    assert report.warnings[0].code == "UNUSUAL_INCUBATION_DURATION"
    assert "outside the recommended range" in report.warnings[0].message


def test_unsupported_plate_type_is_error() -> None:
    protocol = _valid_protocol()
    protocol["plate_type"] = "1536_well"

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert report.errors[0].code == "SCHEMA_VALIDATION_ERROR"
    assert "plate_type" in report.errors[0].message

def test_zero_sample_volume_is_error() -> None:
    protocol = _valid_protocol()
    protocol["samples"][0]["volume_ul"] = 0

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert report.errors[0].code == "SCHEMA_VALIDATION_ERROR"
    assert "samples.0.volume_ul" in report.errors[0].message

def test_schema_error_prevents_reagent_checks() -> None:
    protocol = _valid_protocol()
    protocol["samples"][0]["volume_ul"] = 0
    protocol["steps"][0]["reagent"] = "nonexistent_reagent"

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert report.errors[0].code == "SCHEMA_VALIDATION_ERROR"
    assert "samples.0.volume_ul" in report.errors[0].message

    error_codes = [issue.code for issue in report.errors]
    assert "UNKNOWN_REAGENT" not in error_codes

def test_insufficient_reagent_volume_is_error() -> None:
    protocol = _valid_protocol()
    protocol["reagents"][0]["volume_ul"] = 99

    report = validate_protocol_data(protocol)
    assert not report.is_valid
    assert report.errors[0].code == "INSUFFICIENT_REAGENT_VOLUME"
    assert "reagents.0.volume_ul" in report.errors[0].message
    
def test_repeated_dispenses_exceed_available_reagent() -> None:
    protocol = _valid_protocol()
    protocol["reagents"][0]["volume_ul"] = 150

    second_dispense = protocol["steps"][0].copy()
    protocol["steps"].append(second_dispense)

    report = validate_protocol_data(protocol)

    assert not report.is_valid
    assert report.errors[0].code == "INSUFFICIENT_REAGENT_VOLUME"
    assert "reagents.0.volume_ul" in report.errors[0].message

def test_all_wells_dispense_counts_each_defined_well() -> None:
    protocol = _valid_protocol()
    protocol["reagents"][0]["volume_ul"] = 150

    second_sample = protocol["samples"][0].copy()
    # Give the copy a different ID and well, then append it.

    second_sample["id"] = "sample_002"
    second_sample["well"] = "A2"
    protocol["samples"].append(second_sample)

    report = validate_protocol_data(protocol)
    # Assert the expected result and issue code.
    assert not report.is_valid
    assert report.errors[0].code == "INSUFFICIENT_REAGENT_VOLUME"
    assert "reagents.0.volume_ul" in report.errors[0].message

def test_reagent_volume_budget() -> None:
    protocol = _valid_protocol()
    protocol["reagents"][0]["volume_ul"] = 150

    # Create second reagent copy and give it a separate id. Volume stays at 150uL
    second_reagent = protocol["reagents"][0].copy()
    second_reagent["name"] = "phosphate_buffered_saline"
    second_reagent["volume_ul"] = 150 #Ensure the volume of the second reagent is 150uL
    protocol["reagents"].append(second_reagent)

    # Create second step with newly defined reagent 
    second_step = protocol["steps"][0].copy()
    second_step["reagent"]="phosphate_buffered_saline"
    protocol["steps"].append(second_step)

    report = validate_protocol_data(protocol)
    # Assert the expected result and issue code.
    assert report.is_valid
    assert report.errors == []