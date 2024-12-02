import paho.mqtt.client as mqtt
import json

# MQTT Configuration
BROKER = "localhost"
PORT = 1883
INPUT_TOPICS = ["submarine/sonar", "submarine/power", "submarine/rudder", "submarine/weapons"]
OUTPUT_TOPIC = "submarine/dashboard"

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

        # Log updates
        #print(f"Updated System Status: {system_status}")
        #print(f"Overall System Status: {overall_status}")

        # Publish to dashboard
        dashboard_payload = json.dumps({
            "Status": overall_status,
            "Details": system_status
        })
        client.publish(OUTPUT_TOPIC, dashboard_payload)
        print(f"AGGREGATOR OUT: {payload}")
        print(f"Published to dashboard: {dashboard_payload}")

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
