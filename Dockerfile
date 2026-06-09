# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS builder
WORKDIR /app
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS runtime
WORKDIR /app
ENV PATH="/app/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
COPY --from=builder --chown=10001:10001 /app/venv /app/venv
COPY --chown=10001:10001 app/ /app/app/
USER 10001
EXPOSE 3000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
