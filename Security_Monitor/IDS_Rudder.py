import pandas as pd
import pickle
import json
import paho.mqtt.client as mqtt
import warnings

# Suppress specific FutureWarnings
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="Passing literal json to 'read_json' is deprecated"
)


# MQTT Configuration
BROKER = "localhost"  # Replace with your broker's address
PORT = 1883
INPUT_TOPIC = "submarine/rudder_input"
OUTPUT_TOPIC = "submarine/rudder"

# Load the trained model
def load_model(model_path):
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    return model

# Preprocessing: Group data into chunks of 10 and extract features
def extract_features(data):
    features = []
    for i in range(0, len(data)):
        chunk = data.iloc[i:i+10]
        if len(chunk) < 10:
            break
        # Compute statistical features
        mean_heading = chunk['heading'].mean()
        std_heading = chunk['heading'].std()
        min_heading = chunk['heading'].min()
        max_heading = chunk['heading'].max()
        range_heading = max_heading - min_heading

        mean_angle = chunk['rudder angle'].mean()
        std_angle = chunk['rudder angle'].std()
        min_angle = chunk['rudder angle'].min()
        max_angle = chunk['rudder angle'].max()
        range_angle = max_angle - min_angle

        mean_power = chunk['rudder power'].mean()
        std_power = chunk['rudder power'].std()
        min_power = chunk['rudder power'].min()
        max_power = chunk['rudder power'].max()
        range_power = max_power - min_power

        # Append features
        features.append([
            mean_heading, std_heading, min_heading, max_heading, range_heading,
            mean_angle, std_angle, min_angle, max_angle, range_angle,
            mean_power, std_power, min_power, max_power, range_power
        ])
    
    # Return as DataFrame
    feature_columns = [
        'mean_heading', 'std_heading', 'min_heading', 'max_heading', 'range_heading',
        'mean_angle', 'std_angle', 'min_angle', 'max_angle', 'range_angle',
        'mean_power', 'std_power', 'min_power', 'max_power', 'range_power'
    ]
    return pd.DataFrame(features, columns=feature_columns)

def evaluate_rudder_data(model, chunk):
    """
    Evaluate a chunk of rudder data and return predictions.
    """
    features = extract_features(chunk)
    predictions = model.predict(features)
    return predictions

def publish_prediction(client, prediction):
    """
    Publish the prediction to the aggregator.
    """
    payload = {
        "Prediction": prediction
    }
    client.publish(OUTPUT_TOPIC, json.dumps(payload))
    #print(f"Published: {payload}")

def on_message(client, userdata, msg):
    """
    Handle incoming rudder data and evaluate it using the model.
    """
    try:
        # Decode the incoming message
        payload = json.loads(msg.payload.decode())
        chunk_data = pd.read_json(payload["Data"], orient="records")
        
        # Ensure required columns exist
        required_columns = ['heading', 'rudder angle', 'rudder power']
        for col in required_columns:
            if col not in chunk_data.columns:
                raise ValueError(f"The input data must contain a '{col}' column.")

        # Evaluate the data
        predictions = evaluate_rudder_data(userdata["model"], chunk_data)
        
        # Publish predictions
        for prediction in predictions:
            publish_prediction(client, prediction)

    except Exception as e:
        print(f"Error processing message: {e}")

if __name__ == "__main__":
    # Load the trained model
    model_path = "IDS_rudder.pkl"
    print("Loading model...")
    rf_model = load_model(model_path)

    # Initialize MQTT client
    client = mqtt.Client(client_id="Rudder_IDS", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1, userdata={"model": rf_model})

    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Subscribe to the rudder input topic
    client.subscribe(INPUT_TOPIC)

    print("Rudder IDS is running and waiting for incoming data...")
    client.loop_forever()
