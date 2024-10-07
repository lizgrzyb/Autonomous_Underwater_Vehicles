# Battleship Simulator and OPCUA Services

This repository contains Docker configurations for setting up and running a Battleship Simulator alongside OPCUA Server and Client services. It also includes the setup for Thingsboard service.

### What is OPCUA?

OPC UA (Open Platform Communications Unified Architecture) is a communication protocol for industrial automation developed by the OPC Foundation. It's designed to be platform-independent and ensures the secure and reliable exchange of data in industrial environments. 

OPC UA is a modern industrial communication protocol that provides a secure, interoperable, and scalable solution for industrial automation and data exchange, fitting into the broader context of industrial digital transformation and IoT.


## Prerequisites

- Docker installed on your machine.
- Basic understanding of Docker commands and networks.
- X11 forwarding permissions if running GUI applications (applicable for Battleship Simulator).

## Setup and Installation

1. **Clone the Repository**

   Clone this repository to your local machine to get started.

2. **Build Docker Images**

   Use the provided script to build Docker images for the Battleship Simulator, OPCUA Server, and OPCUA Client. This script also builds the Thingsboard service.

   ```bash
   ./docker_create.sh
   ```
This script performs the following actions:

- Builds the Battleship Simulator Docker image.
- Builds the OPCUA Server and Client Docker images.
- Creates a Docker network named kr4k3n_net.

3. **Run the Containers**

After building the images, the script automatically runs the following containers:

- *Thingsboard Service:* Exposed on ports 80, 1883, 7070, and 5683-5688.
- *OPCUA Server:* Available on port 4840.
- *Battleship Simulator:* GUI accessible via X11 forwarding.
- *OPCUA Client:* Communicates within the kr4k3n_net network.

4. **X11 Forwarding for GUI**

For the Battleship Simulator's GUI to display on the host's screen, X11 forwarding is enabled:
   ```bash
   xhost +local:docker
   ```
Ensure your X server is configured to allow connections from Docker containers.

## Usage
- Access the Battleship Simulator GUI on your local machine.
- Interact with the OPCUA Server and Client through their respective ports.
- Manage and monitor services via the Thingsboard interface.

## Network Configuration
The containers communicate over a Docker network named kr4k3n_net. This network allows for isolated communication between the containers.

## Troubleshooting
- If you encounter issues with GUI display, ensure your X11 forwarding is correctly configured.
- For any Docker-related issues, check container logs and Docker network settings.

## Contributing
Contributions to improve the Docker setup or the applications are welcome. Please submit a pull request or open an issue for any bugs or feature requests.
