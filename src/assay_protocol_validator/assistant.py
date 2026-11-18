"""One proposal followed by deterministic checks and revalidation."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Annotated, Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from assay_protocol_validator.validator import ValidationReport, validate_protocol_data


class ReagentEdit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    step_index: int = Field(ge=0)
    field: Literal["reagent"]
    before: str = Field(min_length=1)
    after: str = Field(min_length=1)


class EditProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    outcome: Literal["propose_edit"]
    edit: ReagentEdit


class HumanInputRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    outcome: Literal["request_human_input"]
    reason: str = Field(min_length=1)


RESPONSE_ADAPTER = TypeAdapter(
    Annotated[EditProposal | HumanInputRequest, Field(discriminator="outcome")]
)


class AssistantModel(Protocol):
    """Both simulated and real adapters implement this method."""

    def propose(self, request: dict[str, Any]) -> object: ...


class ModelError(Exception):
    """An adapter could not obtain a usable response."""


class FakeModel:
    """Scripted synthetic-fixture behavior for offline development."""

    def propose(self, request: dict[str, Any]) -> object:
        codes = {issue["code"] for issue in request["report"]["errors"]}
        if codes == {"UNKNOWN_REAGENT"}:
            for step in request["unknown_references"]:
                if (
                    step["reagent"] == "demo_setup_mxi"
                    and "demo_setup_mix" in request["reagent_names"]
                ):
                    return {
                        "outcome": "propose_edit",
                        "edit": {
                            "step_index": step["step_index"],
                            "field": "reagent",
                            "before": "demo_setup_mxi",
                            "after": "demo_setup_mix",
                        },
                    }
        if "INSUFFICIENT_REAGENT_VOLUME" in codes:
            reason = "Confirm the actual available reagent volume with the operator."
        else:
            reason = "Ask the operator to resolve the reported issues."
        return {"outcome": "request_human_input", "reason": reason}


@dataclass
class FixResult:
    outcome: str
    reason: str
    original_report: ValidationReport
    edit: ReagentEdit | None = None
    candidate: dict[str, Any] | None = None
    candidate_report: ValidationReport | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "original_report": self.original_report.to_dict(),
            "edit": self.edit.model_dump() if self.edit else None,
            "candidate_report": (
                self.candidate_report.to_dict() if self.candidate_report else None
            ),
        }


def fix_protocol_data(data: dict[str, Any], model: AssistantModel) -> FixResult:
    report = validate_protocol_data(data)
    if report.is_valid:
        return FixResult("leave_unchanged", "Protocol passes validation.", report)

    codes = {issue.code for issue in report.errors}
    # Schema-invalid input may lack the lists and fields used below.
    reagent_names = []
    unknown_references = []
    if "SCHEMA_VALIDATION_ERROR" not in codes:
        reagent_names = [reagent["name"] for reagent in data["reagents"]]
        unknown_references = [
            {"step_index": index, "reagent": step["reagent"]}
            for index, step in enumerate(data["steps"])
            if step["type"] == "dispense" and step["reagent"] not in reagent_names
        ]
    request = {
        "report": report.to_dict(),
        "reagent_names": reagent_names,
        "unknown_references": unknown_references,
    }
    try:
        response = RESPONSE_ADAPTER.validate_python(model.propose(deepcopy(request)))
    except ValidationError:
        return FixResult("rejected", "Model response does not match the allowed format.", report)
    except ModelError as exc:
        return FixResult("model_error", str(exc), report)

    if isinstance(response, HumanInputRequest):
        return FixResult("request_human_input", response.reason, report)

    edit = response.edit
    allowed_target = {"step_index": edit.step_index, "reagent": edit.before}
    if (
        codes != {"UNKNOWN_REAGENT"}
        or allowed_target not in unknown_references
        or edit.after not in reagent_names
    ):
        return FixResult("rejected", "Edit is outside the supported reference correction.", report, edit)

    candidate = deepcopy(data)
    candidate["steps"][edit.step_index]["reagent"] = edit.after
    candidate_report = validate_protocol_data(candidate)
    if candidate_report.is_valid:
        outcome = "accepted"
        reason = "Proposed correction passes validation and is ready for review."
    else:
        outcome = "failed"
        reason = "Proposed correction still fails validation."
    return FixResult(outcome, reason, report, edit, candidate, candidate_report)
