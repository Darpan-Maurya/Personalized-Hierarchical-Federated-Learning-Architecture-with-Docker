# Use Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy files
COPY client.py .
COPY static /app/static


# Install Flask
RUN pip install flask requests

# Expose the default client port
EXPOSE 5000

# Run the app
CMD ["python", "client.py"]
