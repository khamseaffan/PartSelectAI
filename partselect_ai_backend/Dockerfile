FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Add rust (needed for tiktoken) and build tools
RUN apk add --no-cache \
    curl \
    build-base \
    cargo \
    rust \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

COPY pyproject.toml .

RUN uv sync

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
