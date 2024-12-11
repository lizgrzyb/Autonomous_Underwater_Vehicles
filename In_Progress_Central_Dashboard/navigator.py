import arcade
import sys
import math
import socket
import json
import threading
from cryptography.fernet import Fernet

# Add the path to SimulatorUtilities.py for importing
sys.path.append(r'C:/Users/rishi/Desktop/JHU/Critical Infrastructure Protection/Major Project/Autonomous_Underwater_Vehicles/')
sys.path.append(r'C:/Users/rishi/Desktop/JHU/Critical Infrastructure Protection/Major Project/Autonomous_Underwater_Vehicles/BattleshipSimulator/Models')

from SimulatorUtilities import calculate_heading_from_points


class Navigator(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Navigator", resizable=True)

        # Secure connection setup
        self.server_address = "127.0.0.1"
        self.server_port = 65432

        # Replace with the shared Fernet key from the BattleshipModel server
        self.key = b'tNCCELug8zpKpXIUKaKIdx0H2j2mtFwZuDw_YEGgHT0='
        self.cipher = Fernet(self.key)

        # Initialize display variables
        self.heading = 0
        self.speed = 0
        self.distance_to_target = 0
        self.mission_status = "Idle"
        self.actions = "None"

        # Compass settings
        self.center_x = self.width // 2
        self.center_y = self.height // 2 + 50
        self.radius = 100
        
        # Threading and network data
        self.network_thread = None
        self.running = True  # To control the network thread
        self.network_data = None  # Shared variable for fetched data

    def setup(self):
        """Initialize any necessary variables and start the network thread."""
        self.network_thread = threading.Thread(target=self.fetch_data_from_server)
        self.network_thread.daemon = True  # Ensure the thread exits when the main program exits
        self.network_thread.start()
        
    def fetch_data_from_server(self):
        """
        Continuously fetch and decrypt data from the BattleshipModel server in a separate thread.
        """
        while self.running:
            try:
                # Create a secure connection to the server
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((self.server_address, self.server_port))

                # Receive encrypted data
                # encrypted_data = client_socket.recv(1024)
                unencrypted_data = client_socket.recv(1024)
                client_socket.close()
            
                if not unencrypted_data:
                    print("No data recieved from server.")
                    return

                # Decrypt the data
                #json_data = self.cipher.decrypt(encrypted_data).decode()
                json_data = unencrypted_data.decode()
                data = json.loads(json_data)
                
                self.network_data = data
                
            except Exception as e:
                print(f"Error fetching data from server: {e}")

    def update(self, delta_time):
        """Update all relevant variables and fetch server data."""
        if self.network_data:
            self.heading = self.network_data.get("heading", 0)
            self.speed = self.network_data.get("current_speed", 0)
            self.distance_to_target = self.network_data.get("distance_to_target", 0)  # Placeholder
            self.mission_status = self.network_data.get("actions", "None")

    def draw_compass(self):
        """Draw the compass and its needle."""
        # Draw the compass circle
        arcade.draw_circle_outline(self.center_x, self.center_y, self.radius, arcade.color.WHITE, 5)

        # Draw cardinal directions
        text_offset = 10
        arcade.draw_text("N", self.center_x, self.center_y + self.radius + text_offset, arcade.color.RED, 12, anchor_x="center")
        arcade.draw_text("E", self.center_x + self.radius + text_offset, self.center_y, arcade.color.WHITE, 12, anchor_x="center")
        arcade.draw_text("S", self.center_x, self.center_y - self.radius - text_offset, arcade.color.WHITE, 12, anchor_x="center")
        arcade.draw_text("W", self.center_x - self.radius - text_offset, self.center_y, arcade.color.WHITE, 12, anchor_x="center")

        # Adjust the heading to align 0 degrees with North
        adjusted_angle = 90 - self.heading
        needle_length = self.radius - 20
        angle_rad = math.radians(adjusted_angle)

        # Calculate needle position
        needle_x = self.center_x + needle_length * math.cos(angle_rad)
        needle_y = self.center_y + needle_length * math.sin(angle_rad)

        # Draw the needle
        arcade.draw_line(self.center_x, self.center_y, needle_x, needle_y, arcade.color.RED, 5)

    def on_draw(self):
        """Render the screen."""
        arcade.start_render()

        # Draw the compass
        self.draw_compass()

        # Draw navigation data
        arcade.draw_text(f"Speed: {self.speed:.2f} km/h", 50, self.height // 4, arcade.color.WHITE, 14)
        arcade.draw_text(f"Distance to Target: {self.distance_to_target} km", 50, self.height // 4 - 50, arcade.color.WHITE, 14)
        arcade.draw_text(f"Heading: {self.heading:.2f}°", 50, self.height // 4 - 100, arcade.color.WHITE, 14)
        arcade.draw_text(f"Mission Status: {self.mission_status}", 50, self.height // 4 - 150, arcade.color.WHITE, 14)

    def on_close(self):
        """Gracefully shut down the network thread when the window is closed."""
        self.running = False
        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.join()
        super().on_close()
        
def main():
    """Main function to run the Navigator GUI."""
    window = Navigator()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()