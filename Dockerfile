# Use a base image with Python and Java
FROM python:3.9-slim

# Install Java, jq, and any other required tools
RUN apt-get update && \
    apt-get install -y openjdk-17-jre jq && \
    apt-get clean

# Set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application files
COPY . .

# Make fatoora executable
RUN chmod -R +x /app/zatca-sdk/Apps

# Set environment variable for FATOORA_HOME
ENV FATOORA_HOME=/app/zatca-sdk/Apps

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the FastAPI app with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
