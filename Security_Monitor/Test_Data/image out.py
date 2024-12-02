import torch
from torchvision import transforms, datasets
from PIL import Image
import csv
import os
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


# Define the transformations (same as during training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Load the complete model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.load("resnet18_complete.pth", map_location=device)
model.to(device)
model.eval()  # Set to evaluation mode

# Define class names
class_names = ['Malicious', 'Non-Malicious']  # Replace with your actual class names

# Function to add Gaussian noise to the image tensor
def add_gaussian_noise(image_tensor, mean=0.0, std=0.1):
    noise = torch.randn(image_tensor.size()) * std + mean
    noisy_image = image_tensor + noise
    return torch.clamp(noisy_image, 0, 1)  # Ensure pixel values stay in range [0, 1]

# Function to preprocess, add noise, classify, and save noisy images
def classify_and_save_image(image_path, output_folder, mean=0.0, std=0.1):
    try:
        # Load and preprocess the image
        image = Image.open(image_path).convert('RGB')
        input_tensor = transform(image).unsqueeze(0).to(device)  # Add batch dimension

        # Add Gaussian noise
        noisy_tensor = add_gaussian_noise(input_tensor, mean=mean, std=std)
        
        # Save the noisy image
        noisy_image = transforms.ToPILImage()(noisy_tensor.squeeze(0))  # Convert back to PIL image
        os.makedirs(output_folder, exist_ok=True)
        noisy_image_path = os.path.join(output_folder, os.path.basename(image_path))
        noisy_image.save(noisy_image_path)

        # Classify the noisy image
        with torch.no_grad():
            outputs = model(noisy_tensor)
            _, predicted = torch.max(outputs, 1)
            class_label = class_names[predicted.item()]
        
        return class_label, noisy_image_path
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None, None

# Function to process images one at a time, save noisy images, and log results to CSV
def process_and_save_noisy_images(directory_path, output_csv, noisy_image_folder, mean=0.0, std=0.1):
    # Get all image file paths
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_paths = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith(valid_extensions)]

    if not image_paths:
        print("No images found in the directory.")
        return

    # Open the CSV file for logging
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Image Name', 'Classification', 'Noisy Image Path'])  # Write header

        # Process each image
        for image_path in image_paths:
            class_label, noisy_image_path = classify_and_save_image(image_path, noisy_image_folder, mean=mean, std=std)
            if class_label:
                # Extract the image name (without the directory path)
                image_name = os.path.basename(image_path)
                # Log the result
                writer.writerow([image_name, class_label, noisy_image_path])
                # Print notification
                print(f"Processed {image_name} (with Gaussian noise): Classified as {class_label}. Saved to {noisy_image_path}")

# Example usage
if __name__ == "__main__":
    directory_path = "./Test_Data/Sonar_Malicious"  # Replace with the path to your directory containing images
    output_csv = "classification_results_with_noisy_images.csv"  # CSV file to save the results
    noisy_image_folder = "./Noisy_Images"  # Folder to save the noisy images

    # Add Gaussian noise with mean=0.0 and std=0.2
    process_and_save_noisy_images(directory_path, output_csv, noisy_image_folder, mean=0.0, std=0.2)
    print(f"Classification complete. Results and noisy images saved to {output_csv} and {noisy_image_folder}.")
