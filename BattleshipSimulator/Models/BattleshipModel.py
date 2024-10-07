import BattleshipSimulator.Models.SimulatorUtilities as SimulatorUtilities
import BattleshipSimulator.Supervisor.Navigators as SimulatorNavigators
from BattleshipSimulator.Models.GetterSetter import GetterSetter
from BattleshipSimulator.python_vehicle_simulator.vehicles import frigate
import numpy as np

class BattleshipModel(GetterSetter):
    """
    The main model of the battleship, maintaining the attributes of the ship and its systems.
    
    Attributes:
    -----------
    attributes : dict
        Dictionary to store attributes of each system.
    observers : list
        List of observers (e.g., the view) that get notified when the model changes.
    systems : dict
        Dictionary to store attached systems.
    command_registry : dict
        Dictionary to map commands to systems that handle them.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.subsystems = {}
        
        if "supervisor" in kwargs:
            supervisor_args = [] if "supervisor_args" not in kwargs else kwargs["supervisor_args"]
            supervisor_kwargs = {} if "supervisor_kwargs" not in kwargs else kwargs["supervisor_kwargs"]
            self.supervisor = getattr(SimulatorNavigators, kwargs["supervisor"])(self, *supervisor_args, **supervisor_kwargs)
            self.add_child("Supervisor", self.supervisor)
        else:
            self.supervisor = None
        self.supervisor_override_heading = None
        self.supervisor_override_speed = None
        
        if "collision_avoidance" in kwargs:
            collision_avoidance_args = [] if "collision_avoidance_args" not in kwargs else kwargs["collision_avoidance_args"]
            collision_avoidance_kwargs = {} if "collision_avoidance_kwargs" not in kwargs else kwargs["collision_avoidance_kwargs"]
            self.collision_avoidance = getattr(SimulatorNavigators, kwargs["collision_avoidance"])(self, *collision_avoidance_args, **collision_avoidance_kwargs)
            self.add_child("CollisionAvoidance", self.collision_avoidance)
        else:
            self.collision_avoidance = None
        self.ca_override = False
        self.ca_override_heading = None
        self.ca_override_speed = None
        
        self.geometry = ((-10,50), (10,50), (10,-50), (-10,-50)) if "geometry" not in kwargs else kwargs["geometry"]
        self.x = 0 if "x" not in kwargs else kwargs["x"]
        self.y = 0 if "y" not in kwargs else kwargs["y"]
        self.heading = 0 if "heading" not in kwargs else kwargs["heading"]
        self.current_speed = 0 if "speed" not in kwargs else kwargs["speed"]
        self.world = None if "world" not in kwargs else kwargs["world"]
        self.guardrails = (0,0,5000,5000)
        self.out_of_bounds = False
        self.logging_variables = [
            "x", "y", "actions", "heading", "waypoint_heading", "option_port", "option_starboard", "chosen_direction",
            "user_override", "user_override_heading", "ca_override", "ca_override_heading", "ca_override_speed",
            "supervisor_override_heading", "supervisor_override_speed", "chosen_heading", "current_speed", "out_of_bounds"
        ]
        
        self.command_registry = {}
        self.setup()
    
    def setup(self):
        max_x = 0
        min_x = 0
        max_y = 0
        min_y = 0
        for point in self.geometry:
            max_x = max(max_x, point[0])
            min_x = min(min_x, point[0])
            max_y = max(max_y, point[1])
            min_y = min(min_y, point[1])
        # Center the geometry on 0,0 meters
        transform_x, transform_y = SimulatorUtilities.get_origin_transform(min_x, max_x, min_y, max_y)
        if transform_x != 0 or transform_y != 0:
            self.geometry = SimulatorUtilities.transform_coordinates(self.geometry, transform_x, transform_y)
        self.width = min([abs(max_x) + abs(min_x), abs(max_y) + abs(min_y)])
        self.length = max([abs(max_x) + abs(min_x), abs(max_y) + abs(min_y)])

        self.last_x = self.x
        self.last_y = self.y
        self.last_heading = self.heading
        self.waypoint_heading = self.heading
        self.chosen_heading = self.heading
        self.user_override = False
        self.user_override_heading = None
        self.option_port, self.option_starboard = SimulatorUtilities.calculate_rotation_angles(self.heading, self.chosen_heading)
        self.chosen_direction = "n/a"
        self.action_code = 0
        self.actions = ""
        
        self.vehicle = frigate('headingAutopilot', self.current_speed, self.heading)
        self.vehicle.L = abs(min_y) + abs(max_y)
        self.simData = np.empty( [0, 12 + 2 * self.vehicle.dimU], float)
        self.oldEta = np.array([self.x, self.y, 0, 0, 0, 0], float)
        self.oldU = self.vehicle.u_actual
        self.oldNu = self.vehicle.nu

    def update(self, timedelta):
        """
        Update the X and Y coordinates of the battleship at regular intervals.

        Parameters:
        -----------
        timedelta : float
            The time duration between coordinate updates (in seconds).
        """

        self.ca_override = False
        self.ca_override_heading = None
        self.ca_override_speed = None

        self.user_override = False

        for system in self.subsystems.values():
            system.update(timedelta)
        
        if self.current_speed > 0 and len(self.children["Navigation"].waypoints) > 0:

            # Get the left and right angles
            self.waypoint_heading = SimulatorUtilities.calculate_angle_degrees(self.x, self.y, self.children["Navigation"].waypoints[0][0], self.children["Navigation"].waypoints[0][1])

            self.set_action_code(0)

            # turning logic for determining the best way to take a turn
            # right (starboard) or left (port) is determined by comparing the degrees needed to make it to desired heading
            self.chosen_heading = self.waypoint_heading
            self.option_port, self.option_starboard = SimulatorUtilities.calculate_rotation_angles(self.heading, self.chosen_heading)
            if (self.option_port < self.option_starboard - 10) and self.chosen_direction != "port":
                self.chosen_direction = "port"
                if (self.chosen_heading < 0):
                    self.chosen_heading = self.chosen_heading + 360
            elif (self.option_starboard < self.option_port-10) and self.chosen_direction != "starboard":
                self.chosen_direction = "starboard"
                if (self.chosen_heading > 0):
                    self.chosen_heading = self.chosen_heading - 360
            elif (self.chosen_direction != "port"):
                if (self.chosen_heading > 0):
                    self.chosen_heading = self.chosen_heading - 360
            else:
                if (self.chosen_heading < 0):
                    self.chosen_heading = self.chosen_heading + 360
            # if (self.chosen_direction != "port"):
            #     if (self.chosen_heading > 0):
            #         self.chosen_heading = self.chosen_heading - 360
            # else:
            #     if (self.chosen_heading < 0):
            #         self.chosen_heading = self.chosen_heading + 360
        
            # If there is a supervisor, allow it to make the final decision


            # ML will independently calculate waypoint heading
            # I am going to compare the heading values
            # If the headings are different, stop
            # If the headings are the same, then logic to do the collision avoidance

            # Use the ML to determine if the data has been manipulated
            supervisor_data = {} if self.supervisor is None else self.supervisor.override()
            self.supervisor_override_speed = supervisor_data["speed"] if "speed" in supervisor_data else None
            self.supervisor_override_heading = supervisor_data["heading"] if "heading" in supervisor_data else None

            # If the ML reports a speed of 0, stop the ship immediately
            if "speed" in supervisor_data and supervisor_data["speed"] == 0:
                self.current_speed = 0
                return None
            
            # If the ML's heading is within 2 degrees of the heading we calculated, continue
            if "heading" not in supervisor_data or SimulatorUtilities.is_within_threshold(supervisor_data["heading"], self.waypoint_heading, 2):

                if self.collision_avoidance is not None:
                    ca_override_data = self.collision_avoidance.override()
                    
                    if len(ca_override_data) > 0:
                        self.ca_override = True
                        if "heading" in ca_override_data:
                            self.ca_override_heading = ca_override_data["heading"]
                            self.chosen_heading = self.ca_override_heading
                        if "speed" in ca_override_data:
                            self.ca_override_speed = ca_override_data["speed"]
                
                # The human operator's inputs will always receive priority
                if self.user_override_heading is not None:
                    self.chosen_heading = self.user_override_heading
                    self.user_override = True
                
                if abs(abs(self.chosen_heading) - abs(self.heading)) > 1:
                    self.update_action_code(turning = True)
                
                # Generate the next set of data using the python vehicle simulator
                thisSimData, self.oldEta, self.oldNu, self.oldU = SimulatorUtilities.getNextPosition(self.current_speed, self.chosen_heading, self.oldEta, self.vehicle, timedelta, self.oldNu, self.oldU)
                self.simData = np.vstack([self.simData, thisSimData])

                self.last_x, self.last_y, self.last_heading = self.x, self.y, self.heading
                self.x = float(thisSimData[0][0])
                self.y = float(thisSimData[0][1])
                self.heading = SimulatorUtilities.calculate_angle_degrees(self.last_x, self.last_y, self.x, self.y)

                if (self.last_x, self.last_y) != (self.x, self.y):
                    self.update_action_code(moving = True)
                self.actions = self.translate_action_code(self.action_code)
                        
                # If the ship goes outside of the guardrails, treat it like a collision
                self.out_of_bounds = self.x <= self.guardrails[0] or self.x >= self.guardrails[2] or self.y <= self.guardrails[1] or self.y >= self.guardrails[3]
            
            else:
                self.current_speed = 0
    
    def set_action_code(self, i):
        # The action code is a binary number that represents the states that the ship can be in
        self.action_code = i

    def update_action_code(self, moving = None, turning = None, avoiding = None):
        # True = 1, False = 0, None = unchanged
        for bit_position, action in enumerate([moving, turning, avoiding]):
            if action == True:
                self.action_code |= (1 << bit_position)
            elif action == False:
                self.action_code &= ~(1 << bit_position)
    
    def translate_action_code(self, code):
        actions = []
        for i, b in enumerate(bin(code)[2:]):
            if b == "1":
                match(i):
                    case 0:
                        actions.append("Moving")
                    case 1:
                        actions.append("Turning")
                    case 2:
                        actions.append("Avoiding")
        if len(actions) > 0:
            return ",".join(actions)
        else:
            return ""

    def logging_package(self):
        logging_package = {k: getattr(self, k) for k in self.logging_variables}
        for child_name, child in self.children.items():
            system_log_package = child.logging_package()
            for k, v in system_log_package.items():
                logging_package[f"{child_name}.{k}"] = v
        return logging_package

    def attach_system(self, system_name, system):
        """
        Attach a system to the battleship and register its commands.
        
        Parameters:
        -----------
        system_name : str
            The name of the system.
        system : BattleshipSystem
            The system object.
        """

        self.add_child(system_name, system)
        self.subsystems[system_name] = system
        for command in system.commands():
            if command in self.command_registry:
                raise KeyError(f"Could not attach '{system.__class__.__name__}'; command '{command}' already handled by '{self.command_registry[command].__class__.__name__}'")
            self.command_registry[command] = system

    def handle_command(self, command):
        """
        Route the command to the appropriate system.
        
        Parameters:
        -----------
        command : str
            The command to be executed.
        """
        system = self.command_registry.get(command)
        if system:
            system.handle_command(command)
        else:
            print(f"Warning: No system can handle the command '{command}'!")