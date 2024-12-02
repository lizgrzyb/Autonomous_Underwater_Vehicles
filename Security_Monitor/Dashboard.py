import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import json

# MQTT Configuration
BROKER = "localhost"  # Replace with your MQTT broker address
PORT = 1883
TOPIC = "submarine/dashboard"

# Dashboard class
class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Submarine System Dashboard")
        self.root.geometry("500x500")
        self.root.configure(bg="#d3d3d3")  # Light gray background

        # Add a darker border around the window
        self.root.configure(highlightbackground="gray", highlightthickness=2)

        # Title
        title_label = tk.Label(root, text="Submarine System Dashboard", font=("Helvetica", 18, "bold"), bg="#d3d3d3", fg="black")
        title_label.pack(pady=10)

        # Overall System Status
        self.overall_status_label = tk.Label(root, text="Overall System Status", font=("Helvetica", 16), bg="#d3d3d3", fg="black")
        self.overall_status_label.pack(pady=10)

        self.overall_status_value = tk.Label(root, text="Initializing...", font=("Helvetica", 14), bg="#d3d3d3", fg="black")
        self.overall_status_value.pack(pady=5)

        # System Status Frames
        self.status_frames = {}
        for system in ["Sonar", "Power", "Rudder", "Weapons"]:
            frame = self.create_system_frame(system)
            self.status_frames[system] = frame  # Store the frame dictionary
            frame["frame"].pack(pady=10)  # Pack the actual frame widget

        # Connect to MQTT
        self.client = mqtt.Client(client_id="Dashboard", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(BROKER, PORT, 60)

        # Start MQTT loop in the background
        self.client.loop_start()

    def create_system_frame(self, system_name):
        """
        Create a frame to display the status of a specific system.
        """
        frame = tk.Frame(self.root, bg="#d3d3d3")
        label = tk.Label(frame, text=f"{system_name} System Status", font=("Helvetica", 16), bg="#d3d3d3", fg="black")
        label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        status_label = tk.Label(frame, text="Initializing...", font=("Helvetica", 14), bg="#d3d3d3", fg="black")
        status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        light = tk.Canvas(frame, width=20, height=20, bg="#d3d3d3", highlightthickness=0)
        light_indicator = light.create_oval(5, 5, 15, 15, fill="gray")  # Default to gray
        light.grid(row=0, column=2, padx=10, pady=5)

        return {"frame": frame, "status_label": status_label, "light": light, "light_indicator": light_indicator}

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            client.subscribe(TOPIC)
        else:
            print(f"Failed to connect to MQTT broker. Return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            # Decode the message payload
            payload = json.loads(msg.payload.decode())
            overall_status = payload.get("Status", "Unknown")
            system_details = payload.get("Details", {})

            # Update the overall status
            self.update_overall_status(overall_status)

            # Update individual system statuses
            for system, status in system_details.items():
                self.update_system_status(system, status)
        except Exception as e:
            print(f"Error processing message: {e}")

    def update_overall_status(self, status):
        """
        Update the overall system status on the dashboard.
        """
        self.overall_status_value.config(text=status)
        if status == "Anomalous":
            self.overall_status_value.config(fg="red")
        elif status == "Normal":
            self.overall_status_value.config(fg="green")
        else:
            self.overall_status_value.config(fg="black")

    def update_system_status(self, system, status):
        """
        Update the status of a specific system on the dashboard.
        """
        frame = self.status_frames.get(system)
        if frame:
            # Update status label text and color
            frame["status_label"].config(text=status)
            color = "red" if status == "Attack" else "green" if status == "Normal" else "black"
            frame["status_label"].config(fg=color)

            # Update light indicator color
            frame["light"].itemconfig(frame["light_indicator"], fill=color)


# Main function to run the dashboard
if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()
