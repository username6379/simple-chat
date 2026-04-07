FROM python:3.14.3-alpine

COPY . /app

WORKDIR /app

# Install gcc (needed to compile asyncmy)
RUN apk update && apk add build-base

# Install poetry
RUN apk add pipx && pipx install poetry
ENV PATH="$PATH:/root/.local/bin"

# Install application dependencies
RUN poetry install

# Run server
CMD poetry run uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload