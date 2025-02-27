# Use an official Python base image
FROM python:3.9-slim

# Install system packages needed for msodbcsql17
RUN apt-get update && apt-get install -y curl gnupg apt-transport-https unixodbc-dev
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list | tee /etc/apt/sources.list.d/msprod.list
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Create app directory
WORKDIR /app

# Copy your code into the container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port (Render will set PORT at runtime)
ENV PORT 5000
EXPOSE 5000

# Start command: run gunicorn on your Flask app
CMD gunicorn app:app --bind 0.0.0.0:$PORT
