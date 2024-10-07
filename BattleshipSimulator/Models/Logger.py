from BattleshipSimulator.Models.GetterSetter import GetterSetter
import csv
import os
import zmq
import json
from icecream import ic
ic.configureOutput(includeContext=True, contextAbsPath=True)

class CSVLogger(GetterSetter):
    def __init__(self, filename, zmq_port=5556):
        super().__init__()
        self.filename = filename
        self.ensure_directories_exist(self.filename)
        self.file = open(self.filename, 'w', newline='')
        self.data = []
        self.file_open = True
        self.writer = csv.writer(self.file)

        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{zmq_port}")

    def publish_data(self, data):
        try:
            
            json_data = json.dumps(data)
            # ic(json_data)
            self.socket.send_string(json_data)
        except Exception as e:
            print(f"Error publishing data: {e}")
    
    @property
    def length(self):
        return len(self.data)

    def log(self, data):
        # If the file is new (or empty), write the headers (dictionary keys)
        if os.path.getsize(self.filename) == 0:
            
            self.writer.writerow(data.keys())
            self.flush()
        
        # Write the dictionary values
        self.writer.writerow(data.values())
        self.data.append(data)

        # Publish the data
        self.publish_data(data)
    
    def get(self, index):
        if 0 <= index < len(self.data):
            # The original data should be immutable, so make a copy
            return self.data[index].copy()
        else:
            print(index)
            return None

    def flush(self):
        """Ensures that data is written to the file."""
        self.file.flush()

    def close(self):
        if self.file_open:
            self.flush()
            self.file.close()
            self.file_open = False
        
        self.socket.close()
        self.context.term()
    
    def ensure_directories_exist(self, file_path):
        # Extract the directory part of the file path
        directory = os.path.dirname(file_path)
        # Check if the directory already exists
        if not os.path.exists(directory):
            # If it doesn't exist, create it (and any necessary parent directories)
            os.makedirs(directory)

    def rename_file(self, new_name):
        os.rename(self.filename, new_name)
        self.filename = new_name