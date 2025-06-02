# --- Stage 1: Build Stage ---
FROM python:3.11-slim-bookworm AS builder

# Set a temporary working directory for dependency installation
WORKDIR /tmp/build

# Copy the requirements file from your app directory to the build stage
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime Stage ---
FROM python:3.11-slim-bookworm

# Set metadata
LABEL author="Emil Wilawer"
LABEL description="Audio Transcription and Diarization Pipeline"

# Set the primary working directory for your application's code
WORKDIR /app

# Copy the installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Install necessary system dependencies for audio processing
RUN apt-get update && \
    apt install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the contents of your 'app' directory into the container's /app
COPY app/ .

# Set the entrypoint to your main pipeline script
ENTRYPOINT ["python", "pipeline.py"]

# Provide a default command if no arguments are given (e.g., show help)
CMD ["--help"]