import BattleshipSimulator.Models.BattleshipModel as BattleModel
from BattleshipSimulator.Models.GetterSetter import GetterSetter
import BattleshipSimulator.Models.BattleshipSystem as BattleSystem
import BattleshipSimulator.Models.SimulatorUtilities as SimulatorUtilities
from BattleshipSimulator.Models.Logger import CSVLogger
import datetime
import time
import random
import numpy as np
import csv
import pickle
import pandas as pd
from multiprocessing import shared_memory
import json
import paho.mqtt.client as mqtt
import copy
import os

#Operation modes/attacks
NORMAL = 1
GPS_SPOOFING = 2            # Packet count spikes, gps x and y offset have a value
SONAR_JAMMING = 3           # CPU usage and packet count increase
COMMUNICATION_JAMMING = 4   # packet count and network bytes rate drop
MINE = 5                    # Some or all systems shut down
POWER_ATTACK = 6            # power attack
RUDDER_ATTACK = 7           # rudder attack

# CIP begin

class MessageSystem(GetterSetter):
    def __init__(self):
        super().__init__()
        self.hardware_log = []
        self.sonar_log = []
        self.power_sys_log = []

class Hardware(GetterSetter):
    def __init__(self):
        super().__init__()
        self.hardware_data = {
            "CPU Usage": 0,
            "IO Usage": 0,
            "Memory Usage": 0,
            "Process Num": 0,
            "Network Bytes Rate": 0,
            "Packet Count": 0,
            "GPS X Offset": 0,
            "GPS Y Offset": 0,
        }
        self.global_status = NORMAL
        self.counter = 0
        self.counter_to_launch_attack = None
        self.attack_to_launch = None
        self.predicted_attack = 1

        self.gps_x_offset = 0
        self.gps_y_offset = 0

        self.message = MessageSystem()
        self.power = [SimulatorUtilities.calculate_power(3, self.global_status)]             # [watt]
        self.power_log = [copy.deepcopy(self.power)]
        self.rudder_log = []

        # Load the trained ICS Monitor model
        self.model = None
        self.power_data_client = None
        self.rudder_data_client = None
        self.weapon_data_client = None
        self.image_data_client = None
        with open("AI-Models/ICS_TRAINING_V2/ICS_Monitor.pkl", "rb") as file:
            self.model = pickle.load(file)

        try:
            self.shared_mem_aggregator = shared_memory.SharedMemory("aggregator", False, 10)
        except:
            self.shared_mem_aggregator = shared_memory.SharedMemory("aggregator", True, 10)
        self.shared_mem_aggregator_buff = self.shared_mem_aggregator.buf
        self.shared_mem_aggregator_buff[0] = 1

        # Extract and validate feature names
        self.feature_order = list(self.model.feature_names_in_)
        self.validate_features()

        # Initialize CSV files
        self.init_csv_files()

    def validate_features(self):
        """Validate feature names in hardware_data against the model's expected features."""
        hardware_keys = set(self.hardware_data.keys())
        model_keys = set(self.feature_order)

        missing_keys = model_keys - hardware_keys
        extra_keys = hardware_keys - model_keys

        if missing_keys:
            raise ValueError(f"Missing keys in hardware_data: {missing_keys}")
        if extra_keys:
            print(f"Warning: Extra keys in hardware_data (not used in model): {extra_keys}")

    def init_csv_files(self):
        headers = [
            "CPU Usage", "IO Usage", "Memory Usage", "Process Num",
            "Network Bytes Rate", "Packet Count", "GPS X Offset", "GPS Y Offset"
        ]
        attack_types = ["normal", "GPS_SPOOFING", "SONAR_JAMMING", "COMMUNICATION_JAMMING", "MINE"]
        for attack in attack_types:
            with open(f"output_{attack}.csv", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(headers)

    def update(self, timeDelta):
        self.counter += 1

        if (self.counter_to_launch_attack and self.counter == self.counter_to_launch_attack):
            if (self.attack_to_launch is None):
                self.attack_to_launch = random.uniform(2, 5)
            self.global_status = self.attack_to_launch

        # Sync GPS offsets with hardware_data dictionary
        self.hardware_data["GPS X Offset"] = self.gps_x_offset
        self.hardware_data["GPS Y Offset"] = self.gps_y_offset

        # update into the message queue
        self.message.hardware_log.append(self.hardware_data.items())

        # Reorder hardware_data to match feature order in the model
        prediction_data = {key: self.hardware_data[key] for key in self.feature_order}
        data = pd.DataFrame([prediction_data])  # DataFrame with correct feature order

        # Use the model to predict the attack type
        #self.predicted_attack = self.model.predict(data)[0]
        self.predicted_attack = self.shared_mem_aggregator_buff[0]
        print(self.predicted_attack)

        # Alert the detected attack type
        #print(f"Detected Attack: {self.predicted_attack}")
        #print(self.counter, self.counter_to_launch_attack)

        # Write the data to the appropriate CSV file
        values_array = [self.hardware_data[key] for key in self.feature_order]
        with open(f"output\output_{self.predicted_attack}.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(values_array)

        if (self.global_status == POWER_ATTACK):
            with open("output\output_power_attack.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(self.power)
        else:
            with open("output\output_power.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(self.power)

        self.power_log.append(copy.deepcopy(self.power))

        # client send power log to mqtt server
        if (len(self.power_log) >= 10):
            group_log = [self.power_log[-10:]]
            for i, chunk in enumerate(group_log):
                # Convert the chunk to JSON
                chunk = pd.DataFrame(chunk, columns=["Power"])
                chunk_json = chunk.to_json(orient="records")
                payload = json.dumps({"ChunkID": i, "Data": chunk_json})
                #print(payload)

                # Publish the chunk
                #self.power_data_client.publish("submarine/power_input", payload)
                os.system(f"mosquitto_pub -h localhost -t \"submarine/power_input\" -m {payload}")

                #print(payload)


        # Simulate hardware metrics
        self.simulate_hardware_metrics()

        # Apply attack impacts
        self.simulate_attack_impacts()

        self.power[0] = SimulatorUtilities.calculate_power(3, self.global_status)

    def simulate_hardware_metrics(self):
        self.hardware_data["CPU Usage"] = random.uniform(10, 20)
        self.hardware_data["IO Usage"] = random.uniform(5, 15)
        self.hardware_data["Memory Usage"] = random.uniform(15, 30)
        self.hardware_data["Process Num"] = random.uniform(100, 300)
        self.hardware_data["Network Bytes Rate"] = random.uniform(0, 10)
        self.hardware_data["Packet Count"] = random.uniform(200, 500)

    def simulate_attack_impacts(self):
        if self.global_status == GPS_SPOOFING:
            self.hardware_data["Packet Count"] += random.uniform(150, 700)
            self.gps_x_offset += 2
            self.gps_y_offset += 2

        if self.global_status == SONAR_JAMMING:
            self.hardware_data["Packet Count"] += random.uniform(1000, 1500)
            self.hardware_data["CPU Usage"] += random.uniform(20, 40)

        if self.global_status == COMMUNICATION_JAMMING:
            self.hardware_data["Packet Count"] = random.uniform(0, 10)
            self.hardware_data["Network Bytes Rate"] = random.uniform(0, 10)

        if self.global_status == MINE:
            self.hardware_data["CPU Usage"] += random.uniform(50, 90)
            self.hardware_data["Memory Usage"] += random.uniform(100, 200)
            self.hardware_data["Packet Count"] = 0

    def monitor(self):
        try:
            print("Starting real-time monitoring. Press Ctrl+C to stop.")
            while True:
                self.update(1)  # Call update every second
                time.sleep(1)  # Pause for 1 second
        except KeyboardInterrupt:
            print("Real-time monitoring stopped.")

        
        #if self.counter > 1500:
            #self.global_status = GPS_SPOOFING

# CIP end

class Simulator(GetterSetter):

    def __init__(self, config_file, prediction_window=None):  # Add `prediction_window` argument
        super().__init__()
        self.config_file = config_file
        self.success_conditions = {}
        self.failure_conditions = {}
        # Format the date and time in a filename-safe way
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.logger = CSVLogger(f"results/{timestamp}_{SimulatorUtilities.get_filename_without_extension(config_file)}_results.csv")
        
        # set up mqtt server
        BROKER = "localhost"
        PORT = 1883
        TOPIC = "submarine/power_input"
        self.power_data_client = mqtt.Client(client_id="Power_Data_Passer", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.power_data_client.connect(BROKER, PORT, 60)
        self.rudder_data_client = mqtt.Client(client_id="Rudder_Data_Passer", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.rudder_data_client.connect(BROKER, PORT, 60)
        self.weapon_data_client = mqtt.Client(client_id="Weapons_Data_Passer", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.weapon_data_client.connect(BROKER, PORT, 60)
        self.image_data_client = mqtt.Client(client_id="Image_Publisher", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.image_data_client.connect(BROKER, PORT)

        # Pass the prediction_window to Hardware
        self.message = MessageSystem()
        self.hardware = Hardware()    # Pass prediction_window here
        self.hardware.power_data_client = self.power_data_client
        self.hardware.rudder_data_client = self.rudder_data_client
        self.hardware.weapon_data_client = self.weapon_data_client
        self.hardware.image_data_client = self.image_data_client

        self.add_child("Logger", self.logger)
        self.setup()
    
    def setup(self):
        self.total_time = 0
        self.timedelta = 0
        self.logging_variables = ["total_time", "timedelta", "simulation_status"]
        #TODO: move scenario logic outside of the controller, where it belongs
        config_data = SimulatorUtilities.load_yaml(self.config_file)
        # Create the world where the models will exist
        world_kwargs = {} if "world" not in config_data else config_data["world"]
        self.world = World(**world_kwargs)
        self.add_child("World", self.world)
        # Create the models
        if "entities" in config_data:
            for entity in config_data["entities"]:
                # Load the generic config
                battleship_config = SimulatorUtilities.load_yaml(entity["_configuration"])
                # Add or overwrite variables that are in the entity config into the battleship config
                battleship_config = self.recursive_key_update(battleship_config, {k:v for k,v in entity.items() if k[0] != "_"})
                battleship_config["world"] = self.world
                # Manually add battleship system overrides
                if "_attached_systems" in battleship_config:
                    for system_name in battleship_config["_attached_systems"]:
                        if (underscored_system_name := f"_{system_name}") in entity:
                            self.recursive_key_update(battleship_config, {underscored_system_name: entity[underscored_system_name]})
                model = BattleModel.BattleshipModel(**battleship_config)
                model.hardware = self.hardware          # CIP
                if "attack_counters" in config_data:
                    self.hardware.counter_to_launch_attack = int(config_data["attack_counters"])
                if "attack_to_launch" in config_data:
                    self.hardware.attack_to_launch = int(config_data["attack_to_launch"])
                    
                self.world.attach_model(entity["_id"], model)
                for system_name in battleship_config["_attached_systems"]:
                    # Add kwargs if they exist for this system
                    if f"_{system_name}" in battleship_config:
                        getattr(BattleSystem, system_name)(model, **battleship_config[f"_{system_name}"])
                    else:
                        getattr(BattleSystem, system_name)(model)
        # Create the success and fail conditions
        for condition_set in ["success_conditions", "failure_conditions"]:
            if condition_set not in config_data:
                raise RuntimeError("You must have at least one success and failure condition")
            for condition_variable, condition_value in config_data[condition_set].items():
                if condition_set == "success_conditions":
                    self.success_conditions[condition_variable] = condition_value
                else:
                    self.failure_conditions[condition_variable] = condition_value
        self.simulation_running = False
        self.simulation_paused = False
        self.simulation_status = "Unknown"
    
    def update(self, timedelta):
        if self.simulation_running and not self.simulation_paused:
            self.total_time += timedelta
            self.timedelta = timedelta
            self.world.update(timedelta)
            self.hardware.update(timedelta)     # CIP
            # Check for success
            for condition_variable, condition_value in self.success_conditions.items():
                if self.get_attribute(condition_variable) == condition_value:
                    self.terminate(0)
                    break
            # Check for failure (if it hasn't already succeeded)
            if self.simulation_running:
                for condition_variable, condition_value in self.failure_conditions.items():
                    if self.get_attribute(condition_variable) == condition_value:
                        self.terminate(1)
                        break
            if self.simulation_running and self.total_time > (12 * 60 * 60):
                self.terminate(2)
            
            self.logger.log(self.logging_package())
            # Check if the simulator has stopped
            if not self.simulation_running:
                self.logger.close()
                self.logger.rename_file(self.logger.filename[:-4] + f"_{self.simulation_status}.csv")
    
    def start(self):
        self.start_time = time.time()
        self.simulation_running = True
    
    def pause(self):
        self.simulation_paused = True
    
    def resume(self):
        self.simulation_paused = False
    
    def terminate(self, status_code):
        self.simulation_running = False
        match status_code:
            case 0:
                self.simulation_status = "Success"
            case 1:
                self.simulation_status = "Fail-Condition"
            case 2:
                self.simulation_status = "Fail-Timeout"
    
    def restart(self):
        self.__init__(self.config_file)
    
    def logging_package(self):
        logging_package = {k: getattr(self, k) for k in self.logging_variables}
        world_log_package = self.world.logging_package()
        for k, v in world_log_package.items():
            logging_package[f"World.{k}"] = v
        return logging_package

    def recursive_key_update(self, configuration, update_dict):
        for key, value in update_dict.items():
            if type(value) is dict:
                if key not in configuration:
                    configuration[key] = {}
                configuration[key] = self.recursive_key_update(configuration[key], value)
            else:
                configuration[key] = value
        return configuration

class World(GetterSetter):

    def __init__(self, **kwargs):
        super().__init__()
        # Generate objects that are in the way - make this better in the future
        self.obstacles = [] if "obstacles" not in kwargs else kwargs["obstacles"]
        self.logging_variables = []
        self.models = {}
    
    def update(self, timedelta):
        for model in self.models.values():
            model.update(timedelta)
    
    def logging_package(self):
        logging_package = {k: getattr(self, k) for k in self.logging_variables}
        for model_name, model in self.models.items():
            model_log_package = model.logging_package()
            for k, v in model_log_package.items():
                logging_package[f"{model_name}.{k}"] = v
        return logging_package

    def attach_model(self, model_id, model):
        if model_id in self.models:
            raise KeyError(f"The world already has a model with an ID of '{model_id}' assigned")
        self.models[model_id] = model
        self.add_child(model_id, model)