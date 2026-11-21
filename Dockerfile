FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN python -m pip install --no-cache-dir ".[api]"

USER 10001:10001

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "assay_protocol_validator.api:app", "--host", "0.0.0.0", "--port", "8000"]
