# Use Debian Bullseye as base to ensure Java 17 availability
FROM python:3.9-slim-bullseye

# Install required tools: Java 17, jq
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV FATOORA_HOME=/app/zatca-sdk/Apps
ENV PATH="${PATH}:${FATOORA_HOME}"

# Create app directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Ensure fatoora is executable
RUN chmod +x ${FATOORA_HOME}/fatoora

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the app port
EXPOSE 8000

# Start FastAPI with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
