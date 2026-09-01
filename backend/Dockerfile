# Stage 1: Install a pinned digest of cgr.dev/chainguard/python:latest-dev for builder mode
FROM cgr.dev/chainguard/python@sha256:f0f3f01288b7ae009d90828d2dbd2f3c949aa3b6e820081cb278880d758ffb44 AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/build/venv/bin:$PATH"

WORKDIR /build

RUN python -m venv /build/venv
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: install a pinned digest of cgr.dev/chainguard/python:latest for Runtime mode
FROM cgr.dev/chainguard/python@sha256:f47d995d001c1f949d560b1158d7f3ae556aad75a1044e72a125c900c1f05332 AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"


# Copy installed packages from builder
COPY --from=builder /build/venv /venv


# Copy application code — only the self-contained app/ package
COPY app/ ./app/

EXPOSE 8000

USER nonroot

ENTRYPOINT ["python", "-m", "uvicorn"]

CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

