import arcade
import random
import torch
from torchvision import transforms
from PIL import Image
import os
import time

class SonarSystem(arcade.Window):
    def __init__(self, model_path, base_directory):
        super().__init__(850, 600, "Sonar System", resizable=True)
        
        # Load the machine learning model (ensure it's on the GPU if available)
        self.model = torch.load(model_path)
        self.model.eval()
        if torch.cuda.is_available():
            self.model = self.model.cuda()

        self.base_directory = base_directory
        self.image_size = (224, 224)  # Assuming images are resized to 224x224 for model input
        
        # Randomly select initial images
        self.images = self.get_random_images()
        self.target_image = None  # Initially no target image detected
        self.target_label = "No Targets Detected"
        
        # Time tracker for image change
        self.last_update_time = time.time()

    def setup(self):
        pass

    def get_random_images(self):
        # Randomly select images from specified directories
        categories_1 = ["BigAnimals", "Pipes"]
        categories_2 = ["Mines", "Rockets", "Vehicles"]
        
        # Select two images from categories_1 (BigAnimals or Pipes)
        category_1 = random.choice(categories_1)
        category_2 = random.choice(categories_1)
        
        image_1 = self.get_random_image_from_category(category_1)
        image_2 = self.get_random_image_from_category(category_2)
        
        # Select one image from categories_2 (Mines, Rockets, or Vehicles)
        category_3 = random.choice(categories_2)
        image_3 = self.get_random_image_from_category(category_3)
        
        return [image_1, image_2, image_3]
    
    def get_random_image_from_category(self, category):
        # Get random image from a specified category
        category_path = os.path.join(self.base_directory, category)
        images = os.listdir(category_path)
        image_name = random.choice(images)
        return os.path.join(category_path, image_name)
    
    def preprocess_image(self, image_path):
        # Load and preprocess image
        image = Image.open(image_path).convert("RGB")
        transform = transforms.Compose([ 
            transforms.Resize(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        return transform(image).unsqueeze(0).cuda() if torch.cuda.is_available() else transform(image).unsqueeze(0)

    def update(self, delta_time):
        # Change images every 15 seconds
        if time.time() - self.last_update_time >= 10:
            self.last_update_time = time.time()
            self.images = self.get_random_images()
            self.target_label = "No Targets Detected"
            self.target_image = None  # Reset target image
            
            # Classify the images and update the target label
            for image_path in self.images:
                preprocessed_image = self.preprocess_image(image_path)
                output = self.model(preprocessed_image)
                _, predicted_class = torch.max(output, 1)
                
                # Assuming the model predicts class indices (e.g., 0: BigAnimals, 1: Mines, etc.)
                category_name = self.get_category_name(predicted_class.item())
                
                # If the image is classified as Mines, Rockets, or Vehicles, update the label and store image
                if category_name in ["Mines", "Rockets", "Vehicles"]:
                    self.target_label = f"Target Detected: {category_name}"
                    self.target_image = image_path  # Store the target image path

    def get_category_name(self, class_index):
        # Get the class name from the model's output index
        classes = ["BigAnimals", "Mines", "Pipes", "Rockets", "Vehicles"]
        return classes[class_index]

    def on_draw(self):
        arcade.start_render()
        
        # Define x positions for the images (left, center, right)
        x_positions = [120, 420, 720]
        
        # Draw the initial images side by side (top row)
        for i, image_path in enumerate(self.images):
            image = arcade.load_texture(image_path)
            arcade.draw_texture_rectangle(x_positions[i], 420, 200, 200, image)
            
            # Get the category name for each image (this is the directory name)
            category_name = self.get_category_name_from_path(image_path)
            
            # Draw the category name below each image (second row)
            arcade.draw_text(category_name, x_positions[i] - 30, 305, arcade.color.WHITE, 12)
            

        # Draw the "Target" label above the target section
        arcade.draw_text(f"Target: {self.target_label}", 300, 270, arcade.color.AMERICAN_ROSE, 16)
        
        # Draw the target classification label
        # arcade.draw_text(self.target_label, 350, 30, arcade.color.WHITE, 12)

        # If a target image was detected, display it below the "Target" label
        if self.target_image:
            target_texture = arcade.load_texture(self.target_image)
            arcade.draw_texture_rectangle(420, 155, 200, 200, target_texture)
            
    def get_category_name_from_path(self, image_path):
        # Extract the directory name from the image path to get the class name
        class_name = image_path.split(os.sep)[-2]  # Get the second last part of the path (directory name)
        return class_name

def run_sonar_system(model_path, base_directory):
    sonar_system = SonarSystem(model_path, base_directory)
    sonar_system.setup()
    arcade.run()

if __name__ == "__main__":
    model_path = "./assets/ai_models/SonarClassifier.pth"  # Path to your model file
    base_directory = "./assets/SonarImages"  # Path to your base directory containing images
    run_sonar_system(model_path, base_directory)
