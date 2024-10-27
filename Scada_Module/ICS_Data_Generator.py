import csv
import random
import time
import threading

# Define the metrics generation functions for each ICS controller
def generate_metrics():
    return {
        "cpu_percent": random.uniform(10, 30),
        "cpu_time": random.uniform(1000, 5000),
        "memory_usage": random.uniform(500, 2000),
        "network_bytes_rate": random.uniform(100, 500),
        "network_packets_rate": random.uniform(10, 50),
        "network_connections": random.randint(1, 10)
    }

# Function to simulate a controller's operation and log its metrics
def simulate_controller(controller_name, csv_writer):
    metrics = generate_metrics()
    while not stop_event.is_set():
        # Simulate metric changes
        metrics["cpu_percent"] += random.uniform(-1, 1)
        metrics["cpu_time"] += random.uniform(1, 5)
        metrics["memory_usage"] += random.uniform(-50, 50)
        metrics["network_bytes_rate"] += random.uniform(-10, 10)
        metrics["network_packets_rate"] += random.uniform(-5, 5)
        metrics["network_connections"] += random.randint(-1, 1)
        
        # Ensure metrics stay within realistic bounds
        metrics = {
            "cpu_percent": max(0, min(metrics["cpu_percent"], 100)),
            "cpu_time": max(0, metrics["cpu_time"]),
            "memory_usage": max(0, metrics["memory_usage"]),
            "network_bytes_rate": max(0, metrics["network_bytes_rate"]),
            "network_packets_rate": max(0, metrics["network_packets_rate"]),
            "network_connections": max(0, metrics["network_connections"]),
        }
        
        # Write to CSV
        csv_writer.writerow([controller_name] + list(metrics.values()))
        
        # Wait for the next update cycle
        time.sleep(0.5)

# Main function to run the simulation
def run_simulation():
    # Open CSV file
    with open("ics_metrics.csv", mode="w", newline="") as file:
        csv_writer = csv.writer(file)
        # Write header
        csv_writer.writerow(["Controller", "CPU %", "CPU Time", "Memory Usage", "Network Bytes Rate", "Network Packets Rate", "Network Connections"])
        
        # Create threads for each controller
        threads = []
        controllers = ["weapons", "navigation", "propulsion", "power"]
        for controller in controllers:
            thread = threading.Thread(target=simulate_controller, args=(controller, csv_writer))
            threads.append(thread)
            thread.start()
        
        # Wait for user input to stop
        input("Press Enter to stop...\n")
        stop_event.set()
        
        # Join threads
        for thread in threads:
            thread.join()

# Set up a stop event
stop_event = threading.Event()

# Run the simulation
run_simulation()
