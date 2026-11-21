"""HTTP interface for deterministic protocol validation."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from assay_protocol_validator.validator import validate_protocol_data

app = FastAPI(title="Assay Protocol Validator")


@app.post("/validate")
def validate_protocol(protocol: dict) -> JSONResponse:
    report = validate_protocol_data(protocol)
    if report.is_valid:
        status_code = 200
    else:
        status_code = 422

    return JSONResponse(content=report.to_dict(), status_code=status_code)
