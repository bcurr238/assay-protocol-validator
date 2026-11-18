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
- Insufficient reagent volume for `all_wells` dispenses
- Missing step-specific fields

Warnings:

- Incubation durations outside the recommended range of 1 to 240 minutes
- Plate read wavelengths outside the common absorbance range of 300 to 800 nm

For a dispense step with `destination: all_wells`, the validator counts the wells defined in `samples`. The step's `volume_ul` is the amount dispensed per well. For example, dispensing 100 µL per well to two defined wells requires 200 µL. Repeated `all_wells` dispenses using the same reagent draw from its starting volume. If a step requires more than the remaining volume, the validator reports `INSUFFICIENT_REAGENT_VOLUME`.

## Issue Codes

Validation issues include stable codes so other tools do not need to parse English error messages.

Examples:

- `INVALID_WELL`
- `DUPLICATE_SAMPLE_WELL`
- `UNKNOWN_REAGENT`
- `INSUFFICIENT_REAGENT_VOLUME`
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
- Milestone 5: cumulative reagent volume validation
- Milestone 6: labeled synthetic evaluation fixtures

Current milestone:

- Milestone 7: AI-assisted CLI proposals and evaluation

## Roadmap

Future ideas:

- Expose validation through FastAPI and package it with Docker
- Support additional plate formats, such as 384-well plates
- Add configurable validation policies
- Validate sample manifests from CSV files
- Export validation reports to JSON files
- Add AI-assisted protocol review summaries

## Phase 2 AI-assisted CLI

Run these commands from the repository root after installing the package with
`python3 -m pip install -e ".[dev]"`.

```bash
assay-validator fix examples/evaluation/pcr_setup_unknown_reagent.yaml
assay-validator fix examples/evaluation/pcr_setup_cumulative_shortage.yaml
assay-validator examples/valid_normalization_assay.yaml --json
python3 -m pytest
python3 -m assay_protocol_validator.evaluation
```

The `fix` command defaults to a scripted fake model. It validates the loaded
YAML first and skips the model when there are no errors, including when warnings
are present. Otherwise it sends structured issues, declared reagent names, and
unknown references to the model. The response must request human input or propose
one replacement of an unknown dispense reagent reference with a declared name.

The application checks the response format, target, and previous value before
applying the edit to a deep copy. It calls `validate_protocol_data()` on that copy
once and displays the proposed edit and candidate report. The original YAML file
is preserved. A passing candidate receives `accepted`; review the proposal before
manually applying it. A candidate with remaining errors receives `failed`.
Unsupported proposals receive `rejected`. Adapter failures receive `model_error`. Shortages request operator confirmation
of the actual available volume.

`fix` supports `--json`. Exit code 0 means `accepted` or `leave_unchanged`; code 1
means human input is needed, a proposal was rejected or failed, an adapter failed, or parsing failed.
The existing `assay-validator <protocol.yaml> --json` command remains available.
To validate a file literally named `fix`, use `./fix` as its path.

The evaluation runner reads `expected_assistant` labels from the manifest and
reports accepted corrections out of eligible corrections, correct unchanged and
human-input decisions, rejected or failed proposals, and expectation mismatches.
Acceptance in evaluation requires a valid candidate, the intended edit, and exact
preservation of unrelated fields. Cases without assistant labels are counted as
skipped. Reason wording is explanatory and is not scored. The runner exits with
code 1 if an expectation does not match.

These default results evaluate the fake model and application flow.

### Initial evaluation results

The developer's live run on November 17, 2026 used `gpt-6.1-terra` and matched
all three selected assistant expectations. The offline fake-model evaluation
also matched those expectations.

| Metric | Fake model | OpenAI live run |
| --- | --- | --- |
| Accepted corrections / eligible cases | 1 / 1 | 1 / 1 |
| Correct unchanged decisions / expected | 1 / 1 | 1 / 1 |
| Correct human-input decisions / expected | 1 / 1 | 1 / 1 |
| Rejected or failed proposals | 0 | 0 |
| Model errors | 0 | 0 |
| Expectation mismatches | 0 | 0 |

Seven fixtures have deterministic validation labels only and are skipped by the
assistant evaluation. This small initial evaluation demonstrates the selected
decision paths. Automated tests additionally exercise rejected proposals and
corrections that remain invalid. Live results can vary between runs.

### Optional OpenAI adapter

Install the optional SDK in your Python environment and set `OPENAI_API_KEY` in
the terminal environment before running live commands. The application reads the
variable directly. It does not load `.env` files.

```bash
python3 -m pip install -e ".[dev,openai]"
assay-validator fix examples/evaluation/pcr_setup_unknown_reagent.yaml --provider openai
assay-validator fix examples/evaluation/pcr_setup_cumulative_shortage.yaml --provider openai
python3 -m assay_protocol_validator.evaluation --provider openai
```

The default live model is `gpt-6.1-terra`. Set `OPENAI_MODEL` or pass `--model`
with `--provider openai` to select another model supporting Responses and
Structured Outputs. CLI selection takes precedence over the environment.

The adapter sends the validation report, declared reagent names, and unknown
references. It requests a Pydantic-structured decision using the Responses API,
then passes that decision through the same edit checks and revalidation as the
fake model. Evaluation labels are never sent to the model. Valid inputs skip
API calls and credential checks.

Each invalid case makes at most one API call, with a 30-second SDK timeout,
a 4096-token output limit, and automatic retries disabled. Refusals, incomplete
responses, missing credentials, and API failures produce a `model_error` outcome.
Malformed structured decisions are rejected. Responses use `store=False`.

Live runs require API access and incur provider usage charges. Evaluation output
identifies the provider and model and counts model errors separately. Run fake
and live evaluations separately to compare their results. Automated tests use
simulated API responses and require no API key.

API references are available in the [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
and [model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-terra).
