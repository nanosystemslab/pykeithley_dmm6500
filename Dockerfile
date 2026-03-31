FROM python:3.12-slim

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry nox nox-poetry

# Copy project files
COPY pyproject.toml poetry.lock README.md ./
COPY src/ src/
COPY tests/ tests/
COPY noxfile.py ./

# Install dependencies
RUN poetry lock --no-interaction && poetry install --no-interaction

# Default: run tests
CMD ["poetry", "run", "pytest", "tests/", "-v"]
