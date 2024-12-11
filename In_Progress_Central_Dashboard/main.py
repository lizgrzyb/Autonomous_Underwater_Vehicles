import arcade
import multiprocessing
from weapons_system import WeaponsSystem
from navigator import Navigator
from depth_scale import DepthMonitor
from sonar_system import SonarSystem  # Import SonarSystem

def launch_weapons_system():
    window = WeaponsSystem()
    window.setup()
    arcade.run()

def launch_navigator():
    window = Navigator()
    window.setup()
    arcade.run()

def launch_depthmonitor():
    window = DepthMonitor()
    window.setup()
    arcade.run()

def launch_sonar_system():
    sonarImageClassifierPath = "./assets/ai_models/SonarClassifier.pth"  # Path to your model file
    base_directory = "./assets/SonarImages"  # Path to your base directory containing images
    window = SonarSystem(sonarImageClassifierPath, base_directory)
    window.setup()
    arcade.run()

def main():
    # Create separate processes for each window
    process1 = multiprocessing.Process(target=launch_navigator)
    process2 = multiprocessing.Process(target=launch_depthmonitor)
    process3 = multiprocessing.Process(target=launch_weapons_system)
    process4 = multiprocessing.Process(target=launch_sonar_system)  # Add Sonar System process

    # Start all processes
    process1.start()
    process2.start()
    process3.start()
    process4.start()

    # Wait for all processes to finish
    process1.join()
    process2.join()
    process3.join()
    process4.join()

if __name__ == "__main__":
    main()
