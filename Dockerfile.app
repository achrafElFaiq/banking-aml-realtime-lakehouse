FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir \
    faker \
    pydantic \
    psycopg2-binary \
    kafka-python-ng \
    python-dotenv

COPY . .