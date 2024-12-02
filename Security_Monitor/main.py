import subprocess
import os
import signal
import select
import time

# Base directory where the scripts are located
BASE_DIR = "/Users/lizgrzyb/Desktop/CIP_Sub/Security_Monitor"

# Paths to the scripts
IMAGE_PASSER_SCRIPT = os.path.join(BASE_DIR, "EXAMPLE_Sonar.py")
SONAR_IDS_SCRIPT = os.path.join(BASE_DIR, "IDS_Sonar.py")
POWER_PASSER_SCRIPT = os.path.join(BASE_DIR, "EXAMPLE_Power.py")
POWER_IDS_SCRIPT = os.path.join(BASE_DIR, "IDS_Power.py")
RUDDER_PASSER_SCRIPT = os.path.join(BASE_DIR, "EXAMPLE_Rudder.py")
RUDDER_IDS_SCRIPT = os.path.join(BASE_DIR, "IDS_Rudder.py")
WEAPONS_PASSER_SCRIPT = os.path.join(BASE_DIR, "EXAMPLE_Weapons.py")
WEAPONS_IDS_SCRIPT = os.path.join(BASE_DIR, "IDS_Weapons.py")
AGGREGATOR_SCRIPT = os.path.join(BASE_DIR, "Aggregator.py")
DASHBOARD_SCRIPT = os.path.join(BASE_DIR, "dashboard.py")

# Process container
processes = []

def start_process(script_path):
    """
    Start a subprocess for a given script and return it.
    """
    try:
        process = subprocess.Popen(
            ["python3", "-u", script_path],  # -u for unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=BASE_DIR,  # Ensure the working directory is consistent
            text=True  # Capture output as text
        )
        processes.append(process)
        print(f"Started {script_path} (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Failed to start {script_path}: {e}")
        return None

def monitor_processes():
    """
    Monitor processes and stream their output to the main terminal.
    """
    try:
        while True:
            for process in processes:
                # Use select to check if there's output without blocking
                ready, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                for stream in ready:
                    line = stream.readline()
                    if line:
                        if stream == process.stdout:
                            print(line.strip())
                        else:
                            print(f"Error [{process.pid}]: {line.strip()}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nTerminating all processes...")
        stop_all_processes()
        print("All processes have been stopped.")

def stop_all_processes():
    """
    Stop all subprocesses.
    """
    for process in processes:
        try:
            os.kill(process.pid, signal.SIGTERM)
            print(f"Stopped process (PID: {process.pid})")
        except Exception as e:
            print(f"Failed to stop process (PID: {process.pid}): {e}")

if __name__ == "__main__":
    try:
        # Start the Aggregator
        start_process(AGGREGATOR_SCRIPT)
        time.sleep(2)  # Allow the aggregator to initialize

        # Start the Sonar IDS and passer
        start_process(SONAR_IDS_SCRIPT)
        time.sleep(2)  # Allow the IDS to initialize
        start_process(IMAGE_PASSER_SCRIPT)

        # Start the Power IDS and passer
        start_process(POWER_IDS_SCRIPT)
        time.sleep(2)
        start_process(POWER_PASSER_SCRIPT)

        # Start the Rudder IDS and passer
        start_process(RUDDER_IDS_SCRIPT)
        time.sleep(2)
        start_process(RUDDER_PASSER_SCRIPT)

        # Start the Weapons IDS and passer
        start_process(WEAPONS_IDS_SCRIPT)
        time.sleep(2)
        start_process(WEAPONS_PASSER_SCRIPT)

        # Start the Dashboard
        start_process(DASHBOARD_SCRIPT)

        print("\nAll processes are running. Press Ctrl+C to terminate.")

        # Monitor processes and print their output
        monitor_processes()

    except Exception as e:
        print(f"An error occurred: {e}")
        stop_all_processes()
