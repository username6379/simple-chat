FROM python:3.14.3-trixie

# Copy application files to container
COPY . /app

WORKDIR /app

# Install poetry
RUN apt update && apt install -y pipx && pipx install poetry
ENV PATH="$PATH:/root/.local/bin"

# Install application dependencies
RUN poetry install

# Run server
CMD poetry run uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload