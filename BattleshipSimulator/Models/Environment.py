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

#Operation modes/attacks
NORMAL = 1
GPS_SPOOFING = 2 #Packet count spikes, gps x and y offset have a value
SONAR_JAMMING = 3 #CPU usage and packet count increase
COMMUNICATION_JAMMING = 4 #packet count and network bytes rate drop
MINE = 5 #Some or all systems shut down

# CIP begin

class Hardware(GetterSetter):
    def __init__(self):
        super().__init__()
        self.hardware_data = {
            "cpu_usage": 0,
            "io_usage": 0,
            "mem_usage": 0,
            "process_num": 0,
            "network_bytes_rate": 0,
            "packet_count": 0,
            "gps_x_offset": 0,
            "gps_y_offset": 0,
        }
        self.global_status = MINE
        self.counter = 0

        self.gps_x_offset = 0
        self.gps_y_offset = 0

        # Write headers to each CSV file (CPU Usage, IO Usage, Memory Usage, Process num, packet count)
        with open("output_normal.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["CPU Usage", "IO Usage", "Memory Usage", "Process Num", "Network Bytes Rate", "Packet Count", "GPS X Offset", "GPS Y Offset"])
        with open("output_GPS_SPOOFING.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["CPU Usage", "IO Usage", "Memory Usage", "Process Num","Network Bytes Rate", "Packet Count", "GPS X Offset", "GPS Y Offset"])
        with open("output_SONAR_JAMMING.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["CPU Usage", "IO Usage", "Memory Usage", "Process Num","Network Bytes Rate", "Packet Count", "GPS X Offset", "GPS Y Offset"])
        with open("output_COMMUNICATION_JAMMING.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["CPU Usage", "IO Usage", "Memory Usage", "Process Num","Network Bytes Rate", "Packet Count", "GPS X Offset", "GPS Y Offset"])
        with open("output_MINE.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["CPU Usage", "IO Usage", "Memory Usage", "Process Num","Network Bytes Rate", "Packet Count", "GPS X Offset", "GPS Y Offset"])

    def update(self, timeDelta):
        self.counter += 1
        # Sync GPS offsets with hardware_data dictionary
        self.hardware_data["gps_x_offset"] = self.gps_x_offset
        self.hardware_data["gps_y_offset"] = self.gps_y_offset

        values_array = list(self.hardware_data.values())  # Convert to list for CSV writing

        #Determining which output file should be used:
        if self.global_status == NORMAL:
            with open("output_normal.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(values_array)

        if self.global_status == GPS_SPOOFING:
            with open("output_GPS_SPOOFING.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(values_array)
        
        if self.global_status == SONAR_JAMMING:
            with open("output_SONAR_JAMMING.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(values_array)

        if self.global_status == COMMUNICATION_JAMMING:
            with open("output_COMMUNICATION_JAMMING.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(values_array)
        
        if self.global_status == MINE:
            with open("output_MINE.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(values_array)

        else:
            print("Invalid opperating mode selected. Please choose NORMAL, GPS_SPOOFING, SONAR_JAMMING, COMMUNICATION_JAMMING, or MINE")

        #Setting default and normal hardware opperating ranges:
        self.hardware_data["cpu_usage"] = random.uniform(10, 20)
        self.hardware_data["io_usage"] = random.uniform(5, 15)
        self.hardware_data["mem_usage"] = random.uniform(15, 30)
        self.hardware_data["process_num"] = random.uniform(100, 300)
        self.hardware_data["network_bytes_rate"] = random.uniform(0, 10)
        self.hardware_data["packet_count"] = random.uniform(200, 500)

        #Impacts of attacks are captured below:
        if self.global_status == GPS_SPOOFING:
            self.hardware_data["packet_count"] += random.uniform(150, 700)
            self.gps_x_offset += 2
            self.gps_y_offset += 2

        if self.global_status == SONAR_JAMMING:
            self.hardware_data["packet_count"] += random.uniform(1000, 1500)
            self.hardware_data["cpu_usage"] += random.uniform(20, 40)

        if self.global_status == COMMUNICATION_JAMMING:
            self.hardware_data["packet_count"] = random.uniform(0, 10)
            self.hardware_data["network_bytes_rate"] = random.uniform(0, 10)

        if self.global_status == MINE:
            self.hardware_data["cpu_usage"] += random.uniform(50, 90)
            self.hardware_data["mem_usage"] += random.uniform(100, 200)
            self.hardware_data["packet_count"] = 0
        
        
        #if self.counter > 1500:
            #self.global_status = GPS_SPOOFING

# CIP end

class Simulator(GetterSetter):

    def __init__(self, config_file):
        super().__init__()
        self.config_file = config_file
        self.success_conditions = {}
        self.failure_conditions = {}
        # Format the date and time in a filename-safe way
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.logger = CSVLogger(f"results/{timestamp}_{SimulatorUtilities.get_filename_without_extension(config_file)}_results.csv")
        self.hardware = Hardware()    # CIP
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