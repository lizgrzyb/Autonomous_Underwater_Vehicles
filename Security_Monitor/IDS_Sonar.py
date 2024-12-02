import torch
from torchvision import transforms
from PIL import Image
import io
import base64
import json
import paho.mqtt.client as mqtt
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# MQTT Configuration
BROKER = "localhost"  # Replace with your MQTT broker address
PORT = 1883
SONAR_INPUT_TOPIC = "submarine/sonar_input"
SONAR_OUTPUT_TOPIC = "submarine/sonar"

# Define the transformations (same as during training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Load the model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.load("resnet18_complete.pth", map_location=device)
model.to(device)
model.eval()  # Set to evaluation mode

# Define class names
class_names = ['Malicious', 'Non-Malicious']  # Replace with your actual class names

# Function to add Gaussian noise
def add_gaussian_noise(image_tensor, mean=0.0, std=0.1):
    noise = torch.randn(image_tensor.size()) * std + mean
    noisy_image = image_tensor + noise
    return torch.clamp(noisy_image, 0, 1)  # Ensure pixel values stay in range [0, 1]

# Function to classify an image
def classify_image(image_data, mean=0.0, std=0.1):
    try:
        # Decode the base64 image data
        image = Image.open(io.BytesIO(base64.b64decode(image_data))).convert('RGB')

        # Preprocess the image
        input_tensor = transform(image).unsqueeze(0).to(device)

        # Add Gaussian noise
        input_tensor = add_gaussian_noise(input_tensor, mean=mean, std=std)

        # Perform classification
        with torch.no_grad():
            outputs = model(input_tensor)
            _, predicted = torch.max(outputs, 1)
            return class_names[predicted.item()]
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

# Function to handle incoming MQTT messages
def on_message(client, userdata, msg):
    try:
        # Decode the incoming message
        payload = json.loads(msg.payload.decode())
        image_name = payload.get("ImageName", "Unknown")
        image_data = payload.get("ImageData", "")

        # Classify the image
        prediction = classify_image(image_data)

        # Publish the result
        if prediction:
            result = json.dumps({"Image": image_name, "Prediction": prediction})
            client.publish(SONAR_OUTPUT_TOPIC, result)
            #print(f"Processed {image_name}: Classified as {prediction}")
    except Exception as e:
        print(f"Error handling incoming message: {e}")

if __name__ == "__main__":
    # Initialize MQTT client
    client = mqtt.Client(client_id="Sonar_IDS", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Subscribe to the sonar input topic
    client.subscribe(SONAR_INPUT_TOPIC)

    print("Sonar IDS is running and waiting for incoming images...")
    client.loop_forever()
