# Use the official Python 3.10 image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file from the backend folder
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create cache directory for Hugging Face models (transformers)
RUN mkdir -p /app/cache
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache

# Copy the backend code into the container
# This copies everything from the 'backend' folder to '/app'
COPY backend/ .

# Expose port (Hugging Face routes to port 7860 by default)
EXPOSE 7860

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "search_standalone:app", "--host", "0.0.0.0", "--port", "7860"]
