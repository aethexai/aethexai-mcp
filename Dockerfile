FROM python:3.11-slim

WORKDIR /app

# Copy the application code to the container
COPY . .

# Install the package
RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

# Command to run the MCP server
CMD ["aethexai-mcp"]
