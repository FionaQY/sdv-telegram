# Use the official Python image from Docker Hub
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for PyGObject, Cairo, and dbus-python
RUN apt-get update && apt-get install -y \
    libglib2.0-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    build-essential \
    pkg-config \
    libdbus-1-dev \
    libdbus-glib-1-dev \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the local requirements.txt to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application files into the container
COPY . .

# Command to run the bot
CMD ["python", "bot.py"]
