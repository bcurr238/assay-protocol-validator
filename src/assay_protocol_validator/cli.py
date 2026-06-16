"""Command-line interface for the assay protocol validator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from assay_protocol_validator.parser import ProtocolParseError, load_yaml_file
from assay_protocol_validator.validator import ValidationIssue
from assay_protocol_validator.validator import ValidationReport, validate_protocol_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assay-validator",
        description="Validate an assay protocol YAML file.",
    )
    parser.add_argument("protocol_path", type=Path, help="Path to a protocol YAML file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON validation report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        data = load_yaml_file(args.protocol_path)
    except ProtocolParseError as exc:
        report = ValidationReport(errors=[ValidationIssue(message=str(exc))])
        _print_json_report(report) if args.json else _print_report(report)
        return 1

    report = validate_protocol_data(data)
    _print_json_report(report) if args.json else _print_report(report)
    return 0 if report.is_valid else 1


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
