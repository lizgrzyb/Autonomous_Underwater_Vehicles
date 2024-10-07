#!/bin/bash

# Define container names
containers=("thingsboard_service" "opcua_server" "opcua_client" "battleship")

echo "Stopping all containers..."

# Stop all containers
for container in "${containers[@]}"; do
    echo "Stopping $container..."
    docker stop "$container" || echo "$container could not be stopped (might already be stopped)"
done

echo "Removing all containers..."

# Remove all containers
for container in "${containers[@]}"; do
    echo "Removing $container..."
    docker rm "$container" || echo "$container could not be removed (might already be removed)"
done

# Remove Docker network
echo "Removing Docker network 'kr4k3n_net'..."
docker network rm kr4k3n_net || echo "Network 'kr4k3n_net' could not be removed (might already be removed or not exist)"

echo "All containers and network removed."
