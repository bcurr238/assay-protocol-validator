"""Evaluate an assistant against labeled synthetic fixtures."""

import json
from copy import deepcopy
from pathlib import Path

from assay_protocol_validator.assistant import fix_protocol_data
from assay_protocol_validator.openai_model import create_model
from assay_protocol_validator.parser import load_yaml_file


def evaluate_manifest(path: Path, provider: str = "fake", model_name: str | None = None) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    model = create_model(provider, model_name)
    summary = {
        "provider": provider,
        "model": getattr(model, "model_name", "fake"),
        "eligible_corrections": 0,
        "accepted_corrections": 0,
        "expected_unchanged": 0,
        "correct_unchanged": 0,
        "expected_human_input": 0,
        "correct_human_input": 0,
        "rejected_or_failed_proposals": 0,
        "model_errors": 0,
        "mismatches": 0,
        "skipped_unlabeled": 0,
        "cases": [],
    }
    for case in manifest["cases"]:
        expected = case.get("expected_assistant")
        if expected is None:
            summary["skipped_unlabeled"] += 1
            continue
        data = load_yaml_file(path.parent / case["file"])
        result = fix_protocol_data(data, model)
        if expected["outcome"] == "propose_edit":
            summary["eligible_corrections"] += 1
            edit = expected["edit"]
            intended = deepcopy(data)
            intended["steps"][edit["step_index"]][edit["field"]] = edit["after"]
            matches = (
                data["steps"][edit["step_index"]][edit["field"]] == edit["before"]
                and result.outcome == "accepted"
                and result.edit.model_dump() == edit
                and result.candidate_report.is_valid
                and result.candidate == intended
            )
            summary["accepted_corrections"] += int(matches)
        elif expected["outcome"] == "leave_unchanged":
            summary["expected_unchanged"] += 1
            matches = result.outcome == "leave_unchanged" and result.candidate is None
            summary["correct_unchanged"] += int(matches)
        elif expected["outcome"] == "request_human_input":
            summary["expected_human_input"] += 1
            matches = result.outcome == "request_human_input" and result.candidate is None
            summary["correct_human_input"] += int(matches)
        else:
            raise ValueError(f"Unknown expected outcome in {case['file']}")
        summary["rejected_or_failed_proposals"] += int(result.outcome in {"rejected", "failed"})
        summary["model_errors"] += int(result.outcome == "model_error")
        summary["mismatches"] += int(not matches)
        summary["cases"].append({"file": case["file"], "outcome": result.outcome, "reason": result.reason, "matches": matches})
    return summary


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?", default=Path("examples/evaluation/manifest.json"))
    parser.add_argument("--provider", choices=["fake", "openai"], default="fake")
    parser.add_argument("--model", help="OpenAI model name; defaults to OPENAI_MODEL or gpt-6.1-terra.")
    args = parser.parse_args()
    if args.model and args.provider != "openai":
        parser.error("--model requires --provider openai.")
    summary = evaluate_manifest(args.manifest, args.provider, args.model)
    print(json.dumps(summary, indent=2))
    return 1 if summary["mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
