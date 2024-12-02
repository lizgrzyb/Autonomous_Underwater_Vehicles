import pandas as pd
import json
import paho.mqtt.client as mqtt
from joblib import load
import io
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
INPUT_TOPIC = "submarine/weapons_input"
OUTPUT_TOPIC = "submarine/weapons"

# Load the trained model
def load_model(model_path):
    return load(model_path)

# Preprocess the incoming row
def preprocess_row(row_json):
    row = pd.read_json(io.StringIO(row_json), typ="series").to_frame().T
    row.fillna({"Recommended Weapon": "Unknown", "Command Sent": "Unknown"}, inplace=True)

    # Map categorical values
    mappings = {
        "Current Status": {"Unarmed": 0, "Armed": 1},
        "Recommended Weapon": {"Unknown": 0, "Light Torpedo": 1, "Heavy Torpedo": 2},
        "Command Sent": {"Unknown": 0, "Fire": 1},
        "Armed Weapon": {"Light Torpedo": 1, "Heavy Torpedo": 2},
        "Expected Next Status": {"Unarmed": 0, "Armed": 1},
        "Fired?": {"No": 0, "Yes": 1},
    }

    for col, mapping in mappings.items():
        if col in row:
            row[col] = row[col].map(mapping)

    feature_columns = [
        "S.No.",
        "Current Status",
        "Recommended Weapon",
        "Command Sent",
        "Armed Weapon",
        "Expected Next Status",
        "Fired?",
    ]
    return row[feature_columns]

# Handle incoming MQTT messages
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        row_id = payload["RowID"]
        row_json = payload["Data"]

        # Preprocess the row
        processed_row = preprocess_row(row_json)

        # Make prediction
        prediction = model.predict(processed_row)[0]
        prediction_label = "Attack" if prediction == 1 else "Normal"

        # Publish only the prediction to the aggregator
        client.publish(OUTPUT_TOPIC, json.dumps({"Prediction": prediction_label}))
        #print(f"Published prediction to aggregator: {prediction_label}")
    except Exception as e:
        print(f"Error processing row: {e}")

if __name__ == "__main__":
    model_path = "best_adaboost_model.joblib"
    model = load_model(model_path)

    # Initialize MQTT client
    client = mqtt.Client(client_id="Weapons_IDS", protocol=mqtt.MQTTv311)

    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Subscribe to weapons input topic
    client.subscribe(INPUT_TOPIC)

    print("Weapons IDS is running...")
    client.loop_forever()
