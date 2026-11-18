from pathlib import Path

import pytest

from assay_protocol_validator import evaluation
from assay_protocol_validator.evaluation import evaluate_manifest
from assay_protocol_validator.validator import ValidationIssue


def test_selected_manifest_expectations():
    summary = evaluate_manifest(Path("examples/evaluation/manifest.json"))
    assert summary["eligible_corrections"] == summary["accepted_corrections"] == 1
    assert summary["expected_unchanged"] == summary["correct_unchanged"] == 1
    assert summary["expected_human_input"] == summary["correct_human_input"] == 1
    assert summary["mismatches"] == 0
    assert summary["skipped_unlabeled"] == 7


@pytest.mark.parametrize("fault", ["unrelated_field", "wrong_edit", "invalid_candidate"])
def test_evaluation_does_not_accept_incorrect_candidate(monkeypatch, fault):
    original_fix = evaluation.fix_protocol_data

    def faulty_fix(data, model):
        result = original_fix(data, model)
        if result.outcome == "accepted":
            if fault == "unrelated_field":
                result.candidate["assay_name"] = "unexpected_change"
            elif fault == "wrong_edit":
                result.edit.before = "incorrect_original_reference"
            else:
                result.candidate_report.errors.append(
                    ValidationIssue(code="TEST_ERROR", message="Candidate is invalid.")
                )
        return result

    monkeypatch.setattr(evaluation, "fix_protocol_data", faulty_fix)
    summary = evaluate_manifest(Path("examples/evaluation/manifest.json"))
    assert summary["eligible_corrections"] == 1
    assert summary["accepted_corrections"] == 0
    assert summary["mismatches"] == 1
