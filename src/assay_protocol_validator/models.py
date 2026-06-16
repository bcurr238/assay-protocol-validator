"""Pydantic models that describe the supported protocol schema."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlateType(str, Enum):
    """Plate formats supported by the first validator milestone."""

    WELL_96 = "96_well"


class Sample(BaseModel):
    """A biological or experimental sample placed into a plate well."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    well: str = Field(min_length=2)
    volume_ul: float = Field(gt=0)
    donor_id: str = Field(min_length=1)


class Reagent(BaseModel):
    """A named reagent available to workflow steps."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    volume_ul: float = Field(gt=0)


class Step(BaseModel):
    """A workflow step.

    The model validates fields that are required for each supported step type.
    Cross-references, such as whether a reagent exists, are handled by the
    protocol validator because they need access to the full protocol.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["dispense", "incubate", "read_plate"]
    reagent: str | None = None
    destination: str | None = None
    volume_ul: float | None = None
    duration_min: float | None = None
    wavelength_nm: float | None = None

    @model_validator(mode="after")
    def validate_step_fields(self) -> "Step":
        if self.type == "dispense":
            missing = [
                field_name
                for field_name in ("reagent", "destination", "volume_ul")
                if getattr(self, field_name) is None
            ]
            if missing:
                raise ValueError(
                    f"dispense step is missing required field(s): {', '.join(missing)}"
                )
            if self.volume_ul is not None and self.volume_ul <= 0:
                raise ValueError("dispense step volume_ul must be greater than 0")

        if self.type == "incubate":
            if self.duration_min is None:
                raise ValueError("incubate step is missing required field: duration_min")
            if self.duration_min <= 0:
                raise ValueError("incubate step duration_min must be greater than 0")

        if self.type == "read_plate":
            if self.wavelength_nm is None:
                raise ValueError("read_plate step is missing required field: wavelength_nm")
            if self.wavelength_nm <= 0:
                raise ValueError("read_plate step wavelength_nm must be greater than 0")

        return self


class Protocol(BaseModel):
    """Top-level assay protocol model."""

    model_config = ConfigDict(extra="forbid")

    assay_name: str = Field(min_length=1)
    plate_type: PlateType
    samples: list[Sample] = Field(min_length=1)
    reagents: list[Reagent] = Field(min_length=1)
    steps: list[Step] = Field(min_length=1)


def protocol_from_mapping(data: dict[str, Any]) -> Protocol:
    """Build a Protocol from parsed YAML data."""

    return Protocol.model_validate(data)
