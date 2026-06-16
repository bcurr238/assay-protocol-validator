# Assay Protocol Validator

A beginner-friendly, professionally relevant Python CLI for validating assay protocol files before they are used in lab automation workflows.

The first version supports YAML protocol files and checks whether an assay is structurally valid and scientifically/logistically reasonable.

## Why This Project Matters

Lab automation workflows depend on protocol files that describe samples, reagents, plates, and steps. A small typo like an invalid well name, missing sample metadata, or an unknown reagent reference can cause confusing failures later in a workflow.

This project catches those issues early with clear errors and warnings.

It is designed as a public-GitHub-safe portfolio project for learning:

- Python packaging with `pyproject.toml`
- CLI design
- YAML parsing
- Pydantic data validation
- Cross-field validation logic
- pytest-based testing
- LIMS-style and lab automation concepts

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
    test_parser.py
    test_validator.py
```

## Design Decisions

This project uses a `src/` layout because it mirrors how many professional Python packages are structured. It helps tests import the installed package instead of accidentally importing loose files from the project root.

Pydantic is used in `models.py` for field-level validation, such as required fields and positive volumes. This keeps basic data rules close to the data shape.

The `validator.py` module handles cross-field rules, such as duplicate sample wells or a step referencing a reagent that does not exist. These checks need to see the full protocol, so they live outside individual models.

The CLI is intentionally built with Python's standard `argparse` module for the first milestone. That keeps dependencies small while still producing a useful command-line interface.

## Installation

From the project root:

```bash
python -m pip install -e ".[dev]"
```

This installs the package in editable mode, which means changes you make locally are immediately reflected when you run the CLI.

## Usage

Validate a valid protocol:

```bash
assay-validator examples/valid_elisa.yaml
```

Validate an invalid protocol:

```bash
assay-validator examples/invalid_well.yaml
```

You can also run the CLI without installing the console script:

```bash
python -m assay_protocol_validator.cli examples/valid_elisa.yaml
```

## Example Output

For a valid protocol with a warning:

```text
Protocol: cytokine_elisa
Status: VALID

Warnings:
  - Incubation duration of 300 min is outside the recommended range of 1-240 min.
```

For an invalid protocol:

```text
Status: INVALID

Errors:
  - samples.0.well: Well 'Z99' is not valid for plate type '96_well'.
```

## Running Tests

```bash
pytest
```

The tests cover:

- YAML parsing
- Missing files
- Valid protocol behavior
- Invalid well names
- Duplicate sample wells
- Unknown reagent references
- Warning behavior for unusual incubation times

## Current Validation Rules

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

## Sensible Git/GitHub Workflow

For this project, use small milestone branches:

```bash
git checkout -b milestone-01-yaml-validator
git add .
git commit -m "Scaffold assay protocol validator CLI"
git push -u origin milestone-01-yaml-validator
```

Then open a pull request into `main`.

Good future branches:

- `milestone-02-json-support`
- `milestone-03-better-error-reporting`
- `milestone-04-lims-style-sample-manifest`
- `milestone-05-ai-protocol-review`

Each branch should add one clear capability, tests for that capability, and README updates.

## Future Ideas

- JSON support
- Richer plate formats such as 384-well plates
- Configurable validation policies
- CSV sample manifest integration
- Export validation reports as JSON
- GitHub Actions CI
- AI-assisted protocol review summaries
