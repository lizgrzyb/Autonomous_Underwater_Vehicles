# Use the latest Ubuntu image as the base
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

# Install necessary libraries for GUI applications and clean up afterwards
RUN apt-get update && \
    apt-get install -y \
    python3 \
    nano \
    net-tools \
    python3-pip \
    libglu1-mesa-dev \
    freeglut3-dev \
    mesa-common-dev \
    xorg-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint script to start Xvfb and then run the application

CMD ["python3", "/app/main.py"]
