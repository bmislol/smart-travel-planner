# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for lightning-fast package management
RUN pip install uv

# Copy your pyproject.toml
COPY pyproject.toml .

# Install dependencies directly into the system environment (standard for Docker)
RUN uv pip install --system -r pyproject.toml

# Copy the rest of your application code
# (This copies app/, your models, etc., but won't trigger scripts)
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the production server
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]