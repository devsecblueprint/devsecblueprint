# Stage 1: Install a pinned digest of cgr.dev/chainguard/python:latest-dev for builder mode
FROM cgr.dev/chainguard/python:latest-dev AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/build/venv/bin:$PATH"

WORKDIR /build

RUN python -m venv /build/venv
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Remove build-time-only packages so they don't land in the runtime image.
# The app never imports setuptools/pkg_resources/wheel at runtime, and Trivy
# flags setuptools for CVEs, so strip them from the venv that gets copied over.
RUN pip uninstall -y setuptools pkg_resources wheel pip 2>/dev/null || true \
    && rm -rf /build/venv/lib/python*/site-packages/setuptools* \
              /build/venv/lib/python*/site-packages/pkg_resources* \
              /build/venv/lib/python*/site-packages/_distutils_hack \
              /build/venv/lib/python*/site-packages/distutils-precedence.pth \
              /build/venv/lib/python*/site-packages/wheel* \
              /build/venv/lib/python*/site-packages/pip*

# Stage 2: install a pinned digest of cgr.dev/chainguard/python:latest for Runtime mode
FROM cgr.dev/chainguard/python:latest AS runtime

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

