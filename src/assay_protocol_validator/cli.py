"""Command-line interface for the assay protocol validator."""

from __future__ import annotations

import argparse
from pathlib import Path

from assay_protocol_validator.parser import ProtocolParseError, load_yaml_file
from assay_protocol_validator.validator import ValidationReport, validate_protocol_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assay-validator",
        description="Validate an assay protocol YAML file.",
    )
    parser.add_argument("protocol_path", type=Path, help="Path to a protocol YAML file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        data = load_yaml_file(args.protocol_path)
    except ProtocolParseError as exc:
        print("Status: INVALID")
        print("\nErrors:")
        print(f"  - {exc}")
        return 1

    report = validate_protocol_data(data)
    _print_report(report)
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


if __name__ == "__main__":
    raise SystemExit(main())
