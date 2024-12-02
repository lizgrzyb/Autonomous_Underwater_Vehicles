import torch
import numpy as np
import matplotlib.pyplot as plt
from torchvision import transforms
from PIL import Image
import cv2
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# Load the trained model
model_path = "resnet18_complete.pth"  # Adjust to your best model's filename
model = torch.load(model_path, map_location=torch.device('cpu'))
model.eval()

# Define preprocessing (same as used during training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Grad-CAM implementation
def grad_cam(input_image, model, target_layer):
    """
    Perform Grad-CAM on the input image for the specified model and target layer.
    """
    # Forward pass
    feature_maps = []
    gradients = []
    
    def forward_hook(module, input, output):
        feature_maps.append(output)

    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0])

    # Register hooks
    target_layer.register_forward_hook(forward_hook)
    target_layer.register_backward_hook(backward_hook)

    # Prepare input image
    input_tensor = transform(input_image).unsqueeze(0)
    input_tensor.requires_grad = True

    # Perform forward pass
    output = model(input_tensor)
    class_idx = output.argmax(dim=1).item()

    # Perform backward pass
    model.zero_grad()
    output[0, class_idx].backward()

    # Compute Grad-CAM
    gradient = gradients[0].cpu().data.numpy()[0]
    feature_map = feature_maps[0].cpu().data.numpy()[0]
    weights = np.mean(gradient, axis=(1, 2))
    cam = np.sum(weights[:, None, None] * feature_map, axis=0)

    # Normalize and return heatmap
    cam = np.maximum(cam, 0)
    cam = cam / cam.max()
    return cam, class_idx

# Visualize Grad-CAM
def visualize_cam(input_image, cam, class_idx, class_names):
    """
    Visualize the Grad-CAM heatmap on the input image with a grayscale base image and a legend.
    """
    # Normalize and resize the heatmap
    cam_resized = cv2.resize(cam, (224, 224))  # Resize to match input image dimensions
    cam_resized = (cam_resized - cam_resized.min()) / (cam_resized.max() - cam_resized.min())  # Normalize to [0, 1]

    # Convert to heatmap
    heatmap = plt.cm.jet(cam_resized)[..., :3]  # Convert to RGB heatmap

    # Convert input image to grayscale and normalize to [0, 1]
    input_image_gray = np.array(input_image.resize((224, 224)).convert("L")) / 255.0
    input_image_gray = np.stack([input_image_gray] * 3, axis=-1)  # Convert to 3-channel grayscale

    # Overlay heatmap on the grayscale image
    overlay = 0.5 * input_image_gray + 0.5 * heatmap

    # Plot the grayscale image and Grad-CAM heatmap overlay with a legend
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.title("Grayscale Image")
    plt.imshow(input_image_gray, cmap="gray")
    plt.axis("off")
    
    plt.subplot(1, 2, 2)
    plt.title(f"Grad-CAM (Class: {class_names[class_idx]})")
    plt.imshow(overlay)
    plt.axis("off")
    
    # Add a legend for the heatmap
    cbar = plt.colorbar(
        ScalarMappable(norm=Normalize(vmin=0, vmax=1), cmap="jet"),
        ax=plt.gcf().axes[-1],  # Add the colorbar to the last subplot
        orientation="vertical",
        fraction=0.046, pad=0.04  # Adjust size and spacing
    )
    cbar.set_label("Activation Intensity", fontsize=12)
    
    plt.show()
# Example Usage
if __name__ == "__main__":
    # Load an example image
    input_image = Image.open("./Model Training/SONAR/TrainSet/Non-Malicious/00000065.jpg").convert('RGB')  # Replace with your test image path

    # Specify the target layer (e.g., last convolutional layer)
    target_layer = model.layer4[-1]  # Adjust based on your model architecture

    # Perform Grad-CAM
    cam, class_idx = grad_cam(input_image, model, target_layer)

    # Visualize the results
    class_names = ['Malicious', 'Non-Malicious']  # Replace with your actual class names
    visualize_cam(input_image, cam, class_idx, class_names)
