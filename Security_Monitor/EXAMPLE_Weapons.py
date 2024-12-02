import pandas as pd
import json
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "localhost"
PORT = 1883
TOPIC = "submarine/weapons_input"

# Load the weapons data
data_file = "./Test_Data/weapons_test.csv"
data = pd.read_csv(data_file)

# Ensure necessary columns exist
required_columns = ["S.No.", "Current Status", "Recommended Weapon", "Command Sent", "Armed Weapon", "Expected Next Status", "Fired?", "Class"]
for col in required_columns:
    if col not in data.columns:
        raise ValueError(f"The input data must contain a '{col}' column.")

# Initialize MQTT client
client = mqtt.Client(client_id="Weapons_Data_Passer", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

client.connect(BROKER, PORT, 60)

print(f"Starting to send data to {TOPIC}...")

# Send each row of data every second
for index, row in data.iterrows():
    # Convert the row to JSON
    row_json = row.to_json()
    payload = json.dumps({"RowID": row["S.No."], "Data": row_json})

    # Print the payload
    #print(f"Sending payload: {payload}")

    # Publish the payload
    client.publish(TOPIC, payload)

    # Wait 1 second before sending the next row
    time.sleep(1)

print("All data rows sent.")
client.disconnect()
