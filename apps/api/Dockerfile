FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync
COPY src ./src
EXPOSE 8000
