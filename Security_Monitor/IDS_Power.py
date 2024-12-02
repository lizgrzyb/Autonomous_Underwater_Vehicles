import pandas as pd
import pickle
import json
import paho.mqtt.client as mqtt
import os
import warnings

# Suppress specific FutureWarnings
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="Passing literal json to 'read_json' is deprecated"
)


# MQTT Configuration
BROKER = "localhost"
PORT = 1883
INPUT_TOPIC = "submarine/power_input"
OUTPUT_TOPIC = "submarine/power"

# Path to the output CSV file
OUTPUT_CSV = "power_classification_results.csv"

# Initialize the CSV file if it doesn't exist
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "w") as file:
        file.write("ChunkID,PowerValues,Mean,StdDev,Min,Max,Range,Prediction\n")

# Load the trained model
def load_model(model_path):
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    return model

# Preprocessing: Extract features from incoming power data
def extract_features(data):
    features = []
    # Calculate statistical features for the chunk
    avg = data['Power'].mean()
    std = data['Power'].std()
    min_val = data['Power'].min()
    max_val = data['Power'].max()
    range_val = max_val - min_val

    # Append features
    features.append([avg, std, min_val, max_val, range_val])
    
    # Return as DataFrame
    feature_df = pd.DataFrame(features, columns=['Mean', 'StdDev', 'Min', 'Max', 'Range'])
    return feature_df

# Function to log prediction results to CSV
def log_results(chunk_id, power_values, features, prediction):
    """
    Log prediction results to a CSV file.
    """
    with open(OUTPUT_CSV, "a") as file:
        file.write(f"{chunk_id},{power_values},{features['Mean'][0]},{features['StdDev'][0]},{features['Min'][0]},{features['Max'][0]},{features['Range'][0]},{prediction}\n")

# Handle incoming MQTT messages
def on_message(client, userdata, msg):
    try:
        # Decode the incoming message
        payload = json.loads(msg.payload.decode())
        chunk_id = payload.get("ChunkID", -1)
        chunk_data = payload.get("Data", "")

        # Convert JSON string to DataFrame
        data = pd.read_json(chunk_data)

        # Debugging: Print the raw chunk data
        print(f"Chunk {chunk_id} Raw Data:\n{data}")

        # Ensure the input data has the correct column
        if "Power" not in data.columns:
            print(f"Chunk {chunk_id}: Missing 'Power' column. Skipping.")
            return

        # Extract features
        features = extract_features(data)

        # Debugging: Print the extracted features
        print(f"Extracted Features for Chunk {chunk_id}:\n{features}")

        # Make predictions
        predictions = model.predict(features)

        # Get prediction label (assumes binary classification)
        prediction_label = "Normal" if predictions[0] == 0 else "Attack"

        # Debugging: Print predictions
        print(f"Chunk {chunk_id} Prediction: {prediction_label}")

        # Log the results
        log_results(chunk_id, data['Power'].tolist(), features, prediction_label)

        # Publish the result
        result = {"System": "Power", "ChunkID": chunk_id, "Prediction": prediction_label}
        client.publish(OUTPUT_TOPIC, json.dumps(result))
    except Exception as e:
        print(f"Error processing message: {e}")

if __name__ == "__main__":
    # Load the trained model
    model_path = "IDS_power.pkl"
    print("Loading model...")
    model = load_model(model_path)

    # Initialize MQTT client
    client = mqtt.Client(client_id="Power_IDS", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)


    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Subscribe to the power input topic
    client.subscribe(INPUT_TOPIC)

    print("Power IDS is running and waiting for incoming data...")
    client.loop_forever()
