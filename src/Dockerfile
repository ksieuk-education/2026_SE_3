FROM python:3.13-bookworm AS builder

WORKDIR /app

ENV POETRY_VERSION=2.3.2
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV POETRY_VIRTUALENVS_CREATE=true

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-root --only main --no-interaction --no-ansi

FROM python:3.13-slim-bookworm AS runtime-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    netcat-traditional \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /opt/app

COPY --from=builder /app/.venv /opt/app/.venv
COPY lib /opt/app/lib
COPY bin /opt/app/bin

# Образ клиента
FROM runtime-base AS client

COPY ./entrypoint.sh /opt/app/entrypoint.sh
RUN chmod +x /opt/app/entrypoint.sh
