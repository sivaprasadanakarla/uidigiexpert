# Dockerfile
# Use the official Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that Streamlit runs on (default is 8501)
EXPOSE 8501

# Define the entrypoint for the Streamlit application
# We use the PORT environment variable set by Cloud Run and bind to 0.0.0.0
CMD ["streamlit", "run", "dsmain.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

