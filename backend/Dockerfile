FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" \
    || pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings \
       sqlalchemy asyncpg alembic pyjwt redis minio python-multipart

COPY src/ ./src/
COPY alembic.ini ./

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uvicorn", "caf.main:app", "--host", "0.0.0.0", "--port", "8000"]
