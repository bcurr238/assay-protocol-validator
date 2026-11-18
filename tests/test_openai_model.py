import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from assay_protocol_validator.assistant import fix_protocol_data
from assay_protocol_validator.cli import main
from assay_protocol_validator.evaluation import evaluate_manifest
from assay_protocol_validator.openai_model import ModelResponse, OpenAIModel
from assay_protocol_validator.parser import load_yaml_file
from pathlib import Path


@pytest.fixture
def sdk(monkeypatch):
    """Simulate the optional SDK so CI needs no API access or extra package."""
    class APIError(Exception):
        pass

    constructor = MagicMock()
    client = constructor.return_value.__enter__.return_value
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=constructor, APIError=APIError))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    return constructor, client, APIError


def typo_protocol():
    return load_yaml_file("examples/evaluation/pcr_setup_unknown_reagent.yaml")


def test_openai_proposal_passes_through_revalidation(sdk):
    constructor, client, _ = sdk
    client.responses.parse.return_value = SimpleNamespace(
        status="completed",
        output_parsed=ModelResponse.model_validate({"decision": {
            "outcome": "propose_edit",
            "edit": {"step_index": 1, "field": "reagent", "before": "demo_setup_mxi", "after": "demo_setup_mix"},
        }}),
    )
    data = typo_protocol()
    result = fix_protocol_data(data, OpenAIModel("test-model"))
    assert result.outcome == "accepted"
    assert result.candidate_report.is_valid
    assert data["steps"][1]["reagent"] == "demo_setup_mxi"
    constructor.assert_called_once_with(max_retries=0, timeout=30.0)
    client.responses.parse.assert_called_once()
    arguments = client.responses.parse.call_args.kwargs
    assert arguments["model"] == "test-model"
    assert arguments["store"] is False
    assert arguments["text_format"] is ModelResponse
    request = json.loads(arguments["input"])
    assert request["unknown_references"] == [{"step_index": 1, "reagent": "demo_setup_mxi"}]
    assert "expected_assistant" not in request


@pytest.mark.parametrize("status,parsed", [("incomplete", None), ("completed", None)])
def test_unusable_response_is_model_error(sdk, status, parsed):
    _, client, _ = sdk
    client.responses.parse.return_value = SimpleNamespace(status=status, output_parsed=parsed)
    result = fix_protocol_data(typo_protocol(), OpenAIModel())
    assert result.outcome == "model_error"
    assert result.candidate is None


def test_api_error_is_reported_without_provider_body(sdk):
    _, client, error = sdk
    client.responses.parse.side_effect = error("sensitive provider body")
    result = fix_protocol_data(typo_protocol(), OpenAIModel())
    assert result.outcome == "model_error"
    assert "sensitive" not in result.reason
    client.responses.parse.assert_called_once()


def test_invalid_structured_response_is_rejected(sdk):
    _, client, _ = sdk
    with pytest.raises(ValueError) as error:
        ModelResponse.model_validate({"decision": {"outcome": "invented"}})
    client.responses.parse.side_effect = error.value
    result = fix_protocol_data(typo_protocol(), OpenAIModel())
    assert result.outcome == "rejected"


def test_missing_key_and_valid_input_skip(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["fix", "examples/evaluation/pcr_setup_unknown_reagent.yaml", "--provider", "openai", "--json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "model_error"
    assert "OPENAI_API_KEY" in result["reason"]
    assert main(["fix", "examples/evaluation/viability_plate_baseline.yaml", "--provider", "openai", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "leave_unchanged"


def test_openai_evaluation_identifies_provider_and_counts_errors(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    summary = evaluate_manifest(Path("examples/evaluation/manifest.json"), "openai", "test-model")
    assert summary["provider"] == "openai"
    assert summary["model"] == "test-model"
    assert summary["model_errors"] == 2
    assert summary["mismatches"] == 2
    assert summary["correct_unchanged"] == 1
    assert summary["accepted_corrections"] == 0


def test_model_environment_and_cli_override(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "environment-model")
    assert OpenAIModel().model_name == "environment-model"
    assert OpenAIModel("explicit-model").model_name == "explicit-model"


@pytest.mark.parametrize("code,expected", [
    ("insufficient_quota", "billing"),
    ("credit_balance_exhausted", "credit balance"),
    ("organization_spend_limit_exceeded", "organization spend limit"),
    ("project_spend_limit_exceeded", "project spend limit"),
    ("organization_usage_limit_exceeded", "usage limit"),
    ("rate_limit_exceeded", "Wait before retrying"),
    ("slow_down", "Wait before retrying"),
    ("unrecognized_sensitive_code", "cause was not identified"),
    (None, "cause was not identified"),
])
def test_rate_limit_error_explains_cause_without_exposing_body(sdk, code, expected):
    _, client, error_type = sdk
    error = error_type("sensitive provider body")
    error.code = code
    error.status_code = 429
    client.responses.parse.side_effect = error
    result = fix_protocol_data(typo_protocol(), OpenAIModel())
    assert result.outcome == "model_error"
    assert expected in result.reason
    assert "sensitive" not in result.reason
    assert result.candidate is None
    client.responses.parse.assert_called_once()
