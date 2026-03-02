# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port (Cloud Run sets the PORT environment variable)
# Using 8080 as a default fallback
ENV PORT=8080
EXPOSE 8080

# Command to run the application using uvicorn
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
