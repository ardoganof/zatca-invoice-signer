# Dockerfile — Linux + Java + jq + normalize line endings
FROM python:3.11-slim

# Java + jq + dos2unix
RUN apt-get update && apt-get install -y \
      openjdk-21-jre jq dos2unix \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV FATOORA_HOME=/app/zatca-sdk/Apps
ENV PATH="${PATH}:${FATOORA_HOME}"

# Make local SDK importable by Python without installing it to PyPI
ENV PYTHONPATH=/app/zatca-sdk

WORKDIR /app
COPY . .

# Normalize line endings for SDK text + PEMs
RUN find /app/zatca-sdk -type f \
      \( -name "*.json" -o -name "*.xsl" -o -name "*.xsd" -o -name "*.txt" -o -name "*.pem" -o -name "fatoora" \) \
      -exec dos2unix {} \;

# Overwrite Linux fatoora wrapper to:
# - pin working dir to SDK root
# - pass --globalVersion (from global.json)
# - pass --config (defaults.json with Linux paths)
RUN printf '%s\n' '#!/bin/bash' \
                  'set -e' \
                  'FATOORA_HOME=/app/zatca-sdk/Apps' \
                  'SDK_ROOT=/app/zatca-sdk' \
                  'EXTVER=$(jq -r ".version" "${FATOORA_HOME}/global.json")' \
                  'exec java -Duser.dir="${SDK_ROOT}" -Djdk.module.illegalAccess=deny -Djdk.sunec.disableNative=false -jar "${FATOORA_HOME}/zatca-einvoicing-sdk-${EXTVER}.jar" --globalVersion "${EXTVER}" --config "${SDK_ROOT}/Configuration/defaults.json" "$@"' \
      > /app/zatca-sdk/Apps/fatoora && \
    chmod +x /app/zatca-sdk/Apps/fatoora

# Safety symlinks for any internal "../../../" lookups
RUN ln -sf /app/zatca-sdk/Data /app/Data && \
    ln -sf /app/zatca-sdk/Configuration /app/Configuration

# Python deps
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
