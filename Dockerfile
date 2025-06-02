# --- Stage 1: Build Stage (Recommended for Efficiency) ---
FROM python:3.11-slim-bookworm AS builder

# Set a working directory inside the builder stage
WORKDIR /app

# Copy only the requirements file first to leverage Docker's build cache
# Assumes requirements.txt is in the root of your project
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime Stage ---
FROM python:3.11-slim-bookworm

# Set metadata (optional but good practice)
LABEL author="Emil Wilawer"
LABEL description="Audio Transcription and Diarization Pipeline"

# Set the working directory for your application
WORKDIR /app

# Copy the installed packages from the builder stage
# This ensures all pip dependencies are available in the final slim image
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copy your entire project directory into the container
# This includes pipeline.py, and any default config/substitutions files
# Ensure your 'config' folder and its contents are included here if you have defaults
COPY . .

# Install necessary system dependencies for audio processing
# ffmpeg for audio handling, libsndfile1 for audio file reading/writing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        # Add any other system dependencies your Python packages rely on if needed
    && rm -rf /var/lib/apt/lists/* # Clean up apt cache

# Set the entrypoint to your main pipeline script
# This makes 'docker run <image_name> <args>' directly pass <args> to 'python pipeline.py'
ENTRYPOINT ["python", "pipeline.py"]

# Provide a default command if no arguments are given (e.g., show help)
CMD ["--help"]