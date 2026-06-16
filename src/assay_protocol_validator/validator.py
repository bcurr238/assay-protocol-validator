"""Cross-field validation rules for assay protocols."""

from dataclasses import dataclass, field

from pydantic import ValidationError

from assay_protocol_validator.models import PlateType, Protocol, protocol_from_mapping


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation error or warning."""

    message: str


@dataclass
class ValidationReport:
    """Validation result returned by the validator and consumed by the CLI."""

    protocol_name: str | None = None
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


SUPPORTED_WELLS: dict[PlateType, set[str]] = {
    PlateType.WELL_96: {f"{row}{column}" for row in "ABCDEFGH" for column in range(1, 13)}
}

MIN_RECOMMENDED_INCUBATION_MIN = 1
MAX_RECOMMENDED_INCUBATION_MIN = 240
MIN_COMMON_READ_WAVELENGTH_NM = 300
MAX_COMMON_READ_WAVELENGTH_NM = 800


def validate_protocol_data(data: dict) -> ValidationReport:
    """Validate parsed protocol data and return errors plus warnings."""

    report = ValidationReport(protocol_name=data.get("assay_name"))

    try:
        protocol = protocol_from_mapping(data)
    except ValidationError as exc:
        report.errors.extend(_pydantic_errors_to_issues(exc))
        return report

    report.protocol_name = protocol.assay_name
    _validate_sample_wells(protocol, report)
    _validate_reagent_references(protocol, report)
    _add_scientific_warnings(protocol, report)

    return report


def _pydantic_errors_to_issues(exc: ValidationError) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        prefix = f"{location}: " if location else ""
        issues.append(ValidationIssue(message=f"{prefix}{error['msg']}"))
    return issues


def _validate_sample_wells(protocol: Protocol, report: ValidationReport) -> None:
    supported_wells = SUPPORTED_WELLS[protocol.plate_type]
    occupied_wells: dict[str, str] = {}

    for sample in protocol.samples:
        normalized_well = sample.well.upper()
        if normalized_well not in supported_wells:
            report.errors.append(
                ValidationIssue(
                    message=(
                        f"samples.{sample.id}.well: Well '{sample.well}' is not valid "
                        f"for plate type '{protocol.plate_type.value}'."
                    )
                )
            )
            continue

        if normalized_well in occupied_wells:
            report.errors.append(
                ValidationIssue(
                    message=(
                        f"samples.{sample.id}.well: Duplicate well '{sample.well}' "
                        f"already used by sample '{occupied_wells[normalized_well]}'."
                    )
                )
            )
        else:
            occupied_wells[normalized_well] = sample.id


def _validate_reagent_references(protocol: Protocol, report: ValidationReport) -> None:
    reagent_names = {reagent.name for reagent in protocol.reagents}

    for index, step in enumerate(protocol.steps):
        if step.type != "dispense":
            continue

        if step.reagent not in reagent_names:
            report.errors.append(
                ValidationIssue(
                    message=(
                        f"steps.{index}.reagent: Unknown reagent '{step.reagent}'. "
                        "Define it in the reagents section before referencing it."
                    )
                )
            )


def _add_scientific_warnings(protocol: Protocol, report: ValidationReport) -> None:
    for index, step in enumerate(protocol.steps):
        if step.type == "incubate" and step.duration_min is not None:
            if not (
                MIN_RECOMMENDED_INCUBATION_MIN
                <= step.duration_min
                <= MAX_RECOMMENDED_INCUBATION_MIN
            ):
                report.warnings.append(
                    ValidationIssue(
                        message=(
                            f"steps.{index}.duration_min: Incubation duration of "
                            f"{step.duration_min:g} min is outside the recommended range "
                            f"of {MIN_RECOMMENDED_INCUBATION_MIN}-"
                            f"{MAX_RECOMMENDED_INCUBATION_MIN} min."
                        )
                    )
                )

        if step.type == "read_plate" and step.wavelength_nm is not None:
            if not (
                MIN_COMMON_READ_WAVELENGTH_NM
                <= step.wavelength_nm
                <= MAX_COMMON_READ_WAVELENGTH_NM
            ):
                report.warnings.append(
                    ValidationIssue(
                        message=(
                            f"steps.{index}.wavelength_nm: Read wavelength of "
                            f"{step.wavelength_nm:g} nm is outside the common absorbance "
                            f"range of {MIN_COMMON_READ_WAVELENGTH_NM}-"
                            f"{MAX_COMMON_READ_WAVELENGTH_NM} nm."
                        )
                    )
                )
