FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure to maintain proper module paths
COPY . .

# Remove webui/frontend directory to save space
RUN rm -rf ./webui/frontend

# Install the tunesynctool package in development mode to make it available as a CLI command
RUN pip install -e .

# Make sure the Python path includes the API package location
ENV PYTHONPATH=/app/webui:/app

# Expose port (API will run on port 8000)
EXPOSE 8000

# The API expects to run from inside the webui/api directory for relative imports/static paths
WORKDIR /app/webui/api

# Default command runs the API
# To run the CLI instead, override with: docker run tunesynctool tunesynctool [args]
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
