import pandas as pd
import json
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "localhost"
PORT = 1883
TOPIC = "submarine/rudder_input"

# Load the rudder data
data_file = "./Test_Data/output_rudder_attack.csv"
data = pd.read_csv(data_file)

# Ensure required columns exist
required_columns = ['heading', 'rudder angle', 'rudder power']
for col in required_columns:
    if col not in data.columns:
        raise ValueError(f"The input data must contain a '{col}' column.")

# Group data into chunks for sending
group_size = 10
chunks = [data.iloc[i:i+group_size] for i in range(0, len(data), group_size)]

# Initialize MQTT client
client = mqtt.Client(client_id="Rudder_Data_Passer", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

client.connect(BROKER, PORT, 60)

print(f"Starting to send data to {TOPIC}...")

# Send each chunk of data every second
for i, chunk in enumerate(chunks):
    # Convert the chunk to JSON
    chunk_json = chunk.to_json(orient="records")
    payload = json.dumps({"ChunkID": i, "Data": chunk_json})

    # Publish the chunk
    client.publish(TOPIC, payload)
    #print(f"Sent chunk {i+1}/{len(chunks)}")

    # Wait 1 second before sending the next chunk
    time.sleep(1)

print("All data chunks sent.")
client.disconnect()
