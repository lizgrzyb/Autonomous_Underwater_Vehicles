import pandas as pd
import json
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "localhost"
PORT = 1883
TOPIC = "submarine/power_input"

# Load the power data
data_file = "./Test_Data/new_output_power_attack_1000.csv"
data = pd.read_csv(data_file)

# Ensure the "Power" column exists
if "Power" not in data.columns:
    raise ValueError("The input data must contain a 'Power' column.")

# Group data into chunks for sending
group_size = 10
chunks = [data.iloc[i:i+group_size] for i in range(0, len(data), group_size)]

# Initialize MQTT client
client = mqtt.Client(client_id="Power_Data_Passer", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

client.connect(BROKER, PORT, 60)

print(f"Starting to send data to {TOPIC}...")

# Send each chunk of data every second
for i, chunk in enumerate(chunks):
    # Convert the chunk to JSON
    chunk_json = chunk.to_json(orient="records")
    payload = json.dumps({"ChunkID": i, "Data": chunk_json})
    print(payload)

    # Publish the chunk
    client.publish(TOPIC, payload)
    print(payload)
    #print(f"Sent chunk {i+1}/{len(chunks)}")

    # Wait 1 second before sending the next chunk
    time.sleep(1)

print("All data chunks sent.")
client.disconnect()
