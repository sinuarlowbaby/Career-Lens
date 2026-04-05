FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies using uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

CMD ["uvicorn", "app.main:app", "--host", "[IP_ADDRESS]", "--port", "8000", "--reload"]