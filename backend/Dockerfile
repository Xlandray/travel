FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

# Test and lint dependencies stay out of the runtime image unless requested.
# The `dev` extra rides along so ruff and mypy run at their pinned versions in
# the same place the tests do; running them off the host PATH instead is how you
# end up checking the tree with whatever ruff happens to be installed there.
ARG INSTALL_TEST=false
RUN if [ "$INSTALL_TEST" = "true" ]; then pip install ".[test,dev]"; else pip install .; fi

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
