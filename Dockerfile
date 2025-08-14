# Use Debian Bullseye to ensure Java 17 availability
FROM python:3.9-slim-bullseye

# Install Java 17 and jq
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set FATOORA_HOME to the Certificates folder
ENV FATOORA_HOME=/app/zatca-sdk/Data/Certificates
ENV PATH="${PATH}:${FATOORA_HOME}"

# Create app directory
WORKDIR /app

# Copy all project files
COPY . .

# Ensure fatoora script is executable
RUN chmod +x /app/zatca-sdk/Apps/fatoora

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
