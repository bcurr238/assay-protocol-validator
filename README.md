# Assay Protocol Validator

A Python command-line tool for validating YAML assay protocol files before they are used in lab automation workflows.

> Work in progress: this project is being built incrementally as a public-GitHub-safe portfolio project focused on assay development tooling, lab automation validation, and LIMS-style workflow concepts.

## What It Does

Assay protocols often describe samples, reagents, plate layouts, and workflow steps in structured files. A small typo, such as an invalid well name or an unknown reagent reference, can cause confusing failures later in an automation workflow.

This validator catches those issues early and returns clear human-readable output or machine-readable JSON.

Current capabilities:

- Parse YAML protocol files
- Validate protocol structure with Pydantic
- Validate assay-specific rules across samples, reagents, wells, and steps
- Report errors and warnings separately
- Return stable issue codes for downstream tools
- Print human-readable CLI output
- Print JSON output for automation and integrations
- Include example valid and invalid protocols
- Include pytest coverage
- Run automated tests with GitHub Actions CI

## Example Protocol

```yaml
assay_name: cytokine_elisa
plate_type: 96_well
samples:
  - id: sample_001
    well: A1
    volume_ul: 50
    donor_id: donor_123
reagents:
  - name: capture_antibody
    volume_ul: 1000
steps:
  - type: dispense
    reagent: capture_antibody
    destination: all_wells
    volume_ul: 100
  - type: incubate
    duration_min: 60
  - type: read_plate
    wavelength_nm: 450
```

## Installation

From the project root:

```bash
python3 -m pip install -e ".[dev]"
```

This installs the package in editable mode, so local code changes are immediately reflected when you run the CLI.

## Usage

Validate a protocol:

```bash
assay-validator examples/valid_elisa.yaml
```

Validate an invalid protocol:

```bash
assay-validator examples/invalid_well.yaml
```

Print a machine-readable JSON report:

```bash
assay-validator examples/invalid_well.yaml --json
```

You can also run the CLI as a Python module:

```bash
python3 -m assay_protocol_validator.cli examples/valid_elisa.yaml
```

## Example Output

Human-readable output:

```text
Protocol: cytokine_elisa_invalid_well
Status: INVALID

Errors:
  - samples.sample_001.well: Well 'Z99' is not valid for plate type '96_well'.
```

JSON output:

```json
{
  "protocol_name": "cytokine_elisa_invalid_well",
  "status": "invalid",
  "errors": [
    {
      "code": "INVALID_WELL",
      "message": "samples.sample_001.well: Well 'Z99' is not valid for plate type '96_well'."
    }
  ],
  "warnings": []
}
```

## Validation Rules

Errors:

- Unsupported plate types
- Invalid well names
- Missing required fields
- Negative or zero sample and reagent volumes
- Negative or zero dispense volumes
- Duplicate sample wells
- Unknown reagents referenced by dispense steps
- Missing step-specific fields

Warnings:

- Incubation durations outside the recommended range of 1 to 240 minutes
- Plate read wavelengths outside the common absorbance range of 300 to 800 nm

## Issue Codes

Validation issues include stable codes so other tools do not need to parse English error messages.

Examples:

- `INVALID_WELL`
- `DUPLICATE_SAMPLE_WELL`
- `UNKNOWN_REAGENT`
- `SCHEMA_VALIDATION_ERROR`
- `UNUSUAL_INCUBATION_DURATION`
- `UNUSUAL_READ_WAVELENGTH`
- `PROTOCOL_PARSE_ERROR`

This is useful for CI pipelines, LIMS-style systems, scheduling tools, web apps, or future AI-assisted protocol review workflows.

## Project Structure

```text
assay-protocol-validator/
  README.md
  pyproject.toml
  src/
    assay_protocol_validator/
      __init__.py
      cli.py
      models.py
      parser.py
      validator.py
  examples/
    valid_elisa.yaml
    invalid_missing_metadata.yaml
    invalid_well.yaml
  tests/
    test_cli.py
    test_parser.py
    test_validator.py
```

## Design Notes

This project uses a `src/` layout because it mirrors how many professional Python packages are structured. It helps tests import the installed package instead of accidentally importing loose files from the project root.

Pydantic is used in `models.py` for schema and field-level validation, such as required fields, supported step types, and positive volumes.

The `validator.py` module handles cross-field rules, such as duplicate sample wells or a dispense step referencing a reagent that does not exist. These checks need access to the full protocol, so they live outside the individual Pydantic models.

The CLI is built with Python's standard `argparse` module for now. That keeps the project beginner-friendly while still supporting a professional command-line interface.

## Running Tests

```bash
python3 -m pytest
```

The tests cover:

- YAML parsing
- Missing files
- Valid protocol behavior
- Invalid well names
- Duplicate sample wells
- Unknown reagent references
- Warning behavior for unusual incubation times
- JSON CLI output

## Development Workflow

This project is built in small milestone branches:

```bash
git checkout main
git pull
git checkout -b milestone-04-github-actions-ci
```

Each milestone should:

- Add one clear capability
- Include focused tests
- Update the README when behavior changes
- Be reviewed through a pull request before merging into `main`

Completed milestones:

- Milestone 1: YAML protocol validator CLI
- Milestone 2: JSON output
- Milestone 3: issue codes in validation reports
- Milestone 4: GitHub Actions CI

Planned milestones:

- Milestone 5: additional domain validation rules
- Milestone 6: JSON protocol file support
- Milestone 7: validation report export
- Milestone 8: plate map summaries

## Roadmap

Future ideas:

- Support additional plate formats, such as 384-well plates
- Add configurable validation policies
- Validate reagent volume sufficiency
- Validate sample manifests from CSV files
- Export validation reports to JSON files
- Add AI-assisted protocol review summaries
