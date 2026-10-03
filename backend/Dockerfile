# Stage 1: Install a pinned digest of cgr.dev/chainguard/python:latest-dev for builder mode
FROM cgr.dev/chainguard/python@sha256:96cb9c155159daf6b21e70555f244081909ff161c5589112ddf308624c1a1c77 AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/build/venv/bin:$PATH"

WORKDIR /build

RUN python -m venv /build/venv
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: install a pinned digest of cgr.dev/chainguard/python:latest for Runtime mode
FROM cgr.dev/chainguard/python@sha256:1961420e5f93bd056d4b0b40eca12cdf01b3ed09177aa4d6ec71fab38cbf158f AS runtime

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

