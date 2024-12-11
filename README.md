# An Autonomic Security Approach for Enhancing Resilience in Next Generation Attack Submarines
Created by Liz Grzyb, Zeyin (Gin) Zhang, Rishi Bothra and Atharva Nitin-Chaundhari

This is the code base for group 2 in Critical Infrastructure Protection, fall 2024.
This project builds on a battleship simulator, which can be found here:
https://github.com/TechGeek001/Battleship-Simulator

# Run
The security monitor and base submarine simulator are designed to be run seperately and communicate with eachother via MQTT.
### Step 1:
Download this repo and execute commands from the base directory "Autonomous_Underwater_Vehicles".

### Step 2:
From the base directory, run the security monitor with:
python Security_Monitor/main.py

### Step 3:
Run the simulator with: 
python main.py --scenario scenarios/scenario-gen-1.yaml
