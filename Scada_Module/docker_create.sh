#!/bin/bash

# Exit script if any command fails
set -e

# Build Battleship Simulator
echo "Building Battleship Simulator..."
docker build -t kr4k3n-docker_battleship_simulator -f Dockerfile.BattleshipSimulator .

# Build OPCUA_Server
echo "Building OPCUA_Server..."
sudo docker build -t kr4k3n-docker_opcua_server -f Dockerfile.OPCUAServer .

# Build OPCUA_Client
echo "Building OPCUA_Client..."
sudo docker build -t kr4k3n-docker_opcua_client -f Dockerfile.OPCUAClient .

# Create Docker Network
echo "Creating Docker network 'kr4k3n_net'..."
docker network create kr4k3n_net || echo "Network 'kr4k3n_net' already exists"

# Run Thingsboard
echo "Running Thingsboard service..."
docker run -d --name thingsboard_service -p 80:9090 -p 1883:1883 -p 7070:7070 -p 5683-5688:5683-5688/udp -e TB_QUEUE_TYPE=in-memory -v /.mytb-data:/data -v /.mytb-logs:/var/log/thingsboard --network kr4k3n_net --network-alias kr4k3n.thingsboard.io thingsboard/tb-postgres

sleep 30 

# Run OPCUA Server
echo "Running OPCUA Server..."
docker run -d --name opcua_server -p 4840:4840 --network kr4k3n_net kr4k3n-docker_opcua_server

sleep 30 

# Enable connections from your local Docker Container Server
xhost +local:docker

# Run Battleship Docker Container
echo "Running Battleship Docker Container..."
docker run -d --name battleship -p 5556:5556 -e DISPLAY=${DISPLAY} -v /tmp/.X11-unix:/tmp/.X11-unix --network kr4k3n_net kr4k3n-docker_battleship_simulator

sleep 60

# Run OPCUA Client
echo "Running OPCUA Client..."
docker run -d --name opcua_client --network kr4k3n_net kr4k3n-docker_opcua_client
echo "All containers are up and running."


