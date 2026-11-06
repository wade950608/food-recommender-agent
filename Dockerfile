FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project
COPY agent ./agent
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
