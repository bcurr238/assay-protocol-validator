"""Command-line interface for the assay protocol validator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from assay_protocol_validator.assistant import FixResult, fix_protocol_data
from assay_protocol_validator.openai_model import create_model
from assay_protocol_validator.parser import ProtocolParseError, load_yaml_file
from assay_protocol_validator.validator import ValidationIssue
from assay_protocol_validator.validator import ValidationReport, validate_protocol_data


def build_parser(*, fix: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assay-validator fix" if fix else "assay-validator",
        description="Review a proposed protocol correction." if fix else "Validate an assay protocol YAML file.",
    )
    parser.add_argument("protocol_path", type=Path, help="Path to a protocol YAML file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON validation report.",
    )
    if fix:
        parser.add_argument("--provider", choices=["fake", "openai"], default="fake")
        parser.add_argument("--model", help="OpenAI model name; defaults to OPENAI_MODEL or gpt-6.1-terra.")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    fix = bool(arguments and arguments[0] == "fix")
    parser = build_parser(fix=fix)
    args = parser.parse_args(arguments[1:] if fix else arguments)
    if fix:
        try:
            model = create_model(args.provider, args.model)
        except ValueError as exc:
            parser.error(str(exc))

    try:
        data = load_yaml_file(args.protocol_path)
    except ProtocolParseError as exc:
        report = ValidationReport(
            errors=[ValidationIssue(code="PROTOCOL_PARSE_ERROR", message=str(exc))]
        )
        _print_json_report(report) if args.json else _print_report(report)
        return 1

    if fix:
        result = fix_protocol_data(data, model)
        model_name = getattr(model, "model_name", "fake")
        if args.json:
            print(json.dumps({"provider": args.provider, "model": model_name, **result.to_dict()}, indent=2))
        else:
            _print_fix_result(result, args.provider, model_name)
        return 0 if result.outcome in {"accepted", "leave_unchanged"} else 1

    report = validate_protocol_data(data)
    _print_json_report(report) if args.json else _print_report(report)
    return 0 if report.is_valid else 1


def _print_fix_result(result: FixResult, provider: str, model_name: str) -> None:
    print(f"Provider: {provider}; model: {model_name}")
    print(f"Outcome: {result.outcome}")
    print(result.reason)
    print("\nOriginal validation")
    _print_report(result.original_report)
    if result.edit:
        edit = result.edit
        print(f"\nProposed change: steps[{edit.step_index}].{edit.field}")
        print(f"  {edit.before!r} -> {edit.after!r}")
    if result.candidate_report:
        print("\nCandidate validation")
        _print_report(result.candidate_report)
    print("\nSource YAML preserved; review the proposal before editing your file.")


def _print_report(report: ValidationReport) -> None:
    if report.protocol_name:
        print(f"Protocol: {report.protocol_name}")

    print(f"Status: {'VALID' if report.is_valid else 'INVALID'}")

    if report.errors:
        print("\nErrors:")
        for issue in report.errors:
            print(f"  - {issue.message}")

    if report.warnings:
        print("\nWarnings:")
        for issue in report.warnings:
            print(f"  - {issue.message}")


def _print_json_report(report: ValidationReport) -> None:
    print(json.dumps(report.to_dict(), indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
