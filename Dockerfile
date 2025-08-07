FROM openjdk:17-slim

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Create app folder
WORKDIR /app

# Copy SDK files and source
COPY zatca-sdk/ zatca-sdk/
COPY app.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Expose port
EXPOSE 8000

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
