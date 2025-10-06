FROM python:3.13-slim

WORKDIR /app

# Copy package files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install package (not editable for Docker)
RUN pip install --no-cache-dir .

# Set entrypoint
ENTRYPOINT ["export-sentry-issue-mcp"]

# Default to STDIO mode
CMD []
