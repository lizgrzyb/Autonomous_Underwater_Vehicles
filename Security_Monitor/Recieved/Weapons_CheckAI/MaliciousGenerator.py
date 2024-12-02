import random
import pandas as pd

def generate_data(rows=5000):
    data = []
    for i in range(rows):
        record = {
            "S.No.": i + 1,  # Incremental unique ID
            "Current Status": random.choice(["Armed", "Unarmed"]),
            "Recommended Weapon": random.choice(["None", "Light Torpedo", "Heavy Torpedo"]),
            "Command Sent": "None",
            "Armed Weapon": random.choice(["Heavy Torpedo", "Light Torpedo"]),
            "Expected Next Status": random.choice(["Unarmed", "Armed"]),
            "Fired?": random.choice(["Yes", "No"]),
            "Class": "Malicious"
        }
        data.append(record)
    return pd.DataFrame(data)

def write_to_csv(file_name="./output.csv", rows=5000):
    new_data = generate_data(rows)
    try:
        # Append to the CSV file if it exists
        with open(file_name, 'a') as f:
            if f.tell() == 0:  # If the file is empty, write the header
                new_data.to_csv(f, index=False, header=True)
            else:
                new_data.to_csv(f, index=False, header=False)
        print(f"{rows} rows appended to {file_name} successfully.")
    except Exception as e:
        print(f"Error writing to {file_name}: {e}")

# Call the function to write or append data
write_to_csv(rows=5000)
