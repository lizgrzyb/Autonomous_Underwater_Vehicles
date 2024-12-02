import os
import time
import base64
import json
import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "localhost"  # Replace with your MQTT broker address
PORT = 1883
TOPIC = "submarine/sonar_input"
INPUT_FOLDER = "./Test_Data/Sonar_Malicious"

def publish_images():
    # Initialize MQTT client
    client = mqtt.Client(client_id="Image_Publisher", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

    client.connect(BROKER, PORT)

    # Get all image file paths
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_paths = [os.path.join(INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(valid_extensions)]

    if not image_paths:
        print("No images found in the directory.")
        return

    # Publish each image
    for image_path in image_paths:
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Create the payload
        payload = json.dumps({
            "ImageName": os.path.basename(image_path),
            "ImageData": encoded_image
        })

        # Publish the payload
        client.publish(TOPIC, payload)
        print(payload)
        #print(f"Published {os.path.basename(image_path)} to topic {TOPIC}")

        # Wait 1 second before sending the next image
        time.sleep(1)

    client.disconnect()

if __name__ == "__main__":
    publish_images()
