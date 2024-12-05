import paho.mqtt.client as mqtt
import json
from multiprocessing import shared_memory

# MQTT Configuration
BROKER = "localhost"
PORT = 1883
INPUT_TOPICS = ["submarine/sonar", "submarine/power", "submarine/rudder", "submarine/weapons"]
OUTPUT_TOPIC = "submarine/dashboard"

#Attack States:
NORMAL = 1
GPS_SPOOFING = 2            # Packet count spikes, gps x and y offset have a value
SONAR_JAMMING = 3           # CPU usage and packet count increase
COMMUNICATION_JAMMING = 4   # packet count and network bytes rate drop
MINE = 5                    # Some or all systems shut down
POWER_ATTACK = 6            # power attack
RUDDER_ATTACK = 7           # rudder attack

# System-wide status
system_status = {
    "Sonar": "Normal",
    "Power": "Normal",
    "Rudder": "Normal",
    "Weapons": "Normal",
}

def on_message(client, userdata, msg):
    """
    Handle incoming messages from the IDS systems and update system status.
    """
    try:
        # Decode the incoming message
        payload = json.loads(msg.payload.decode())
        #print(f"Received raw payload: {msg.payload}")
        
        topic = msg.topic.split("/")[-1].capitalize()  # Get system name from topic (e.g., "Sonar")
        prediction = payload.get("Prediction", "Unknown")

        # Map Sonar-specific predictions to standard ones
        if topic == "Sonar":
            if prediction == "Malicious":
                prediction = "Attack"  # Translate to aggregator standard
            elif prediction == "Non-Malicious":
                prediction = "Normal"

        # Update system status
        if topic in system_status:
            system_status[topic] = prediction

        # Determine overall system status
        overall_status = "Anomalous" if "Attack" in system_status.values() else "Normal"

        try:
            shared_mem_aggregator = shared_memory.SharedMemory("aggregator", False, 10)
        except:
            shared_mem_aggregator = shared_memory.SharedMemory("aggregator", True, 10)
        shared_mem_aggregator_buff = shared_mem_aggregator.buf
        shared_mem_aggregator_buff[0] = 1
        if overall_status == "Normal":
            shared_mem_aggregator_buff[0] = 1
        elif topic == "Sonar":
            shared_mem_aggregator_buff[0] = 3
        elif topic == "Power":
            shared_mem_aggregator_buff[0] = 6
        elif topic == "Rudder":
            shared_mem_aggregator_buff[0] = 7
        print(f"BUFF {shared_mem_aggregator_buff[0]}")
 
 

        # Log updates

        # Publish to dashboard
        dashboard_payload = json.dumps({
            "Status": overall_status,
            "Details": system_status
        })
        client.publish(OUTPUT_TOPIC, dashboard_payload)
    

    except Exception as e:
        print(f"Error processing message: {e}")


def run_aggregator():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Subscribe to IDS topics
    for topic in INPUT_TOPICS:
        client.subscribe(topic)

    print("Aggregator is running...")
    client.loop_forever()

if __name__ == "__main__":
    run_aggregator()
