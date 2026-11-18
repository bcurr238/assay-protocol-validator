from copy import deepcopy

import pytest

from assay_protocol_validator.assistant import FakeModel, fix_protocol_data
from assay_protocol_validator.parser import load_yaml_file


class StubModel:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def propose(self, request):
        self.requests.append(request)
        return self.response


def typo_protocol():
    return load_yaml_file("examples/evaluation/pcr_setup_unknown_reagent.yaml")


def proposal(**changes):
    edit = dict(step_index=1, field="reagent", before="demo_setup_mxi", after="demo_setup_mix")
    edit.update(changes)
    return {"outcome": "propose_edit", "edit": edit}


def test_supported_correction_preserves_every_other_field():
    data = typo_protocol()
    original = deepcopy(data)
    model = StubModel(proposal())
    result = fix_protocol_data(data, model)
    assert result.outcome == "accepted"
    assert result.candidate_report.is_valid
    expected = deepcopy(original)
    expected["steps"][1]["reagent"] = "demo_setup_mix"
    assert result.candidate == expected
    assert data == original
    assert len(model.requests) == 1
    assert model.requests[0]["report"]["errors"][0]["code"] == "UNKNOWN_REAGENT"


@pytest.mark.parametrize("fixture", ["viability_plate_baseline", "viability_long_incubation"])
def test_valid_input_skips_model(fixture):
    model = StubModel(None)
    result = fix_protocol_data(load_yaml_file(f"examples/evaluation/{fixture}.yaml"), model)
    assert result.outcome == "leave_unchanged"
    assert model.requests == []
    assert result.candidate is None


def test_shortage_requests_input():
    data = load_yaml_file("examples/evaluation/pcr_setup_cumulative_shortage.yaml")
    original = deepcopy(data)
    result = fix_protocol_data(data, FakeModel())
    assert result.outcome == "request_human_input"
    assert result.edit is None
    assert result.candidate is None
    assert data == original


@pytest.mark.parametrize("edit", [
    {"field": "volume_ul"},
    {"step_index": -1},
    {"step_index": True},
    {"step_index": 99},
    {"step_index": 0, "before": "demo_setup_mix"},
    {"before": "wrong_previous_value"},
    {"after": "undeclared_reagent"},
    {"extra": "unexpected"},
])
def test_unsupported_proposal_is_rejected(edit):
    data = typo_protocol()
    original = deepcopy(data)
    result = fix_protocol_data(data, StubModel(proposal(**edit)))
    assert result.outcome == "rejected"
    assert result.candidate_report is None
    assert data == original


def test_revalidation_catches_newly_visible_shortage():
    data = typo_protocol()
    data["reagents"][0]["volume_ul"] = 13
    model = StubModel(proposal())
    result = fix_protocol_data(data, model)
    assert result.outcome == "failed"
    assert result.candidate_report.errors[0].code == "INSUFFICIENT_REAGENT_VOLUME"
    assert len(model.requests) == 1
    assert data["steps"][1]["reagent"] == "demo_setup_mxi"


def test_schema_invalid_input_requests_input():
    result = fix_protocol_data({}, FakeModel())
    assert result.outcome == "request_human_input"
    assert result.candidate is None

def test_invented_action ():
    data = typo_protocol()
    model = StubModel({"outcome": "invented_action"})
    result = fix_protocol_data(data, model)
    assert result.outcome == "rejected"
    assert result.candidate is None
