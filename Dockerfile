# Use Debian Bullseye to ensure Java 17 availability
FROM python:3.9-slim-bullseye

# Install Java 17 and jq
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set SDK environment for the CLI
ENV SDK_CONFIG=/opt/render/project/src/zatca-sdk/Configuration/config.json
ENV FATOORA_HOME=/opt/render/project/src/zatca-sdk/Apps

# Create app directory
WORKDIR /app

# Copy all project files (including SDK folders: Apps + Data/Certificates)
COPY . .

# Normalize line endings so the SDK reads text files cleanly on Linux
RUN apt-get update && apt-get install -y dos2unix && \
    find /app/zatca-sdk -type f \
      \( -name "*.json" -o -name "*.xsl" -o -name "*.xsd" -o -name "*.txt" -o -name "fatoora" \) \
      -exec dos2unix {} \; && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Ensure fatoora runs from SDK root and always uses our Linux defaults.json
RUN chmod +x /app/zatca-sdk/Apps/fatoora && \
    printf '%s\n' '#!/bin/bash' \
                  'set -e' \
                  'FATOORA_HOME=/app/zatca-sdk/Apps' \
                  'SDK_ROOT=/app/zatca-sdk' \
                  'EXTVER=$(jq -r ".version" "${FATOORA_HOME}/global.json")' \
                  'exec java -Duser.dir="${SDK_ROOT}" -Djdk.module.illegalAccess=deny -Djdk.sunec.disableNative=false -jar "${FATOORA_HOME}/zatca-einvoicing-sdk-${EXTVER}.jar" --globalVersion "${EXTVER}" -config "${SDK_ROOT}/Configuration/defaults.json" "$@"' \
      > /app/zatca-sdk/Apps/fatoora && \
    chmod +x /app/zatca-sdk/Apps/fatoora


RUN apt-get update && apt-get install -y dos2unix && \
    find /app/zatca-sdk -type f \( -name "*.json" -o -name "*.xsl" -o -name "*.xsd" -o -name "*.txt" -o -name "fatoora" \) -exec dos2unix {} \; && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Make fatoora executable
RUN chmod +x /app/zatca-sdk/Apps/fatoora

# Create compatibility symlinks for SDK's hard-coded "../../../" lookups
RUN ln -sf /app/zatca-sdk/Data /app/Data && \
    ln -sf /app/zatca-sdk/Configuration /app/Configuration

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

