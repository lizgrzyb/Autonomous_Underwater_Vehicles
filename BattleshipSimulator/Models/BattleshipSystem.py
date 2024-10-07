import BattleshipSimulator.Models.SimulatorUtilities as SimulatorUtilities
from BattleshipSimulator.Models.GetterSetter import GetterSetter
from shapely.geometry import Point, Polygon

class BattleshipSystem(GetterSetter):
    """
    Base class for all ship subsystems. Provides a generic structure for individual systems.
    
    Attributes:
    -----------
    name : str
        The name of the system.
    model : BattleshipModel
        Reference to the main battleship model.
    """

    NAME = "BattleshipSystem"

    def __init__(self, model, **kwargs):
        super().__init__()
        self.model = model
        self.logging_variables = []
        self.setup(**kwargs)
        self.model.attach_system(self.NAME, self)
    
    def setup(self, **kwargs):
        pass
    
    def update(self, timedelta):
        pass

    def logging_package(self):
        logged_objects = {}
        for k in self.logging_variables:
            logged_value = getattr(self, k)
            if type(logged_value) is list:
                logged_value = [x for x in logged_value]
            elif type(logged_value) is dict:
                logged_value = {k:v for k,v in logged_value}
            logged_objects[k] = logged_value
            
        return logged_objects

    def commands(self):
        """
        List of commands this system can handle.

        Returns:
        --------
        list
            List of command strings.
        """
        return []

    def handle_command(self, command):
        """
        Handle a specific command.

        Parameters:
        -----------
        command : str
            The command to handle.
        """
        pass

    def update_attribute(self, attr_name, value):
        """
        A utility method to update attributes of this system in the model.

        Parameters:
        -----------
        attr_name : str
            The attribute's name.
        value : Any
            The value to set.
        """
        self.model.set_attribute(self.name, attr_name, value)

class Rudder(BattleshipSystem):
    """Represents the rudder system of the battleship."""
    
    NAME = "Rudder"

    def commands(self):
        return ["TURN_RIGHT", "TURN_LEFT"]

    def handle_command(self, command):
        match command:
            case "TURN_RIGHT":
                self.turn_right()
            case "TURN_LEFT":
                self.turn_left()
            case _:
                print(f"Unrecognized command: {command}")

    def turn_right(self):
        current_angle = self.model.get_attribute(self.name, "angle") or 0
        new_angle = current_angle + 5
        self.update_attribute("angle", new_angle)

    def turn_left(self):
        current_angle = self.model.get_attribute(self.name, "angle") or 0
        new_angle = current_angle - 5
        self.update_attribute("angle", new_angle)

class Engine(BattleshipSystem):
    """Represents the engine system of the battleship."""

    NAME = "Engine"
    
    def setup(self, **kwargs):
        self.min_speed = 0
        self.max_speed = 15 if "max_speed" not in kwargs else kwargs["max_speed"]
        self.acceleration = .5 if "acceleration" not in kwargs else kwargs["acceleration"]
        self.desired_speed = self.model.current_speed if "desired_speed" not in kwargs else kwargs["desired_speed"]
        self.prev_speed = 0
        self.logging_variables = ["desired_speed"]
    
    def update(self, timedelta):
        self.prev_speed = self.model.current_speed
        if not self.model.get_attribute("RadarSonar:collision_event"):
            # Update the ship's current speed
            if self.model.current_speed != self.desired_speed:
                speed_difference = self.desired_speed - self.model.current_speed
                # The acceleration change is the acceleration divided by the timedelta
                acceleration_change = min(self.acceleration * timedelta, abs(speed_difference))
                if speed_difference > 0:
                    self.model.current_speed += acceleration_change
                else:
                    self.model.current_speed -= acceleration_change
        else:
            self.model.current_speed = 0

    def commands(self):
        return ["SET_SPEED"]

    def handle_command(self, command, *args):
        match command:
            case "SET_SPEED":
                self.set_speed(*args)
            case _:
                print(f"Unrecognized command: {command}")

    def set_speed(self, new_speed):
        if self.min_speed <= new_speed <= self.max_speed:
            self.desired_speed = new_speed

class Weapons(BattleshipSystem):
    """Represents the weapons system of the battleship."""

    NAME = "Weapons"

    def setup(self, **kwargs):
        self.targets = []
        self.target_distances = []
        self.has_targets = False
        self.logging_variables = ["targets", "target_distances", "has_targets"]
        if "targets" in kwargs:
            for target in kwargs["targets"]:
                self.add_target(*target)
    
    def update(self, timedelta):
        # Get the distances
        if len(self.targets) > 0:
            self.target_distances = [SimulatorUtilities.distance(target, (self.model.x, self.model.y)) for target in self.targets]
        else:
            self.target_distances = []
    
    def commands(self):
        return ["FIRE"]

    def handle_command(self, command):
        match command:
            case "FIRE":
                self.fire()
            case _:
                print(f"Unrecognized command: {command}")

    def fire(self):
        # Logic to fire weapons
        pass

    def add_target(self, x, y):
        self.targets.append((x, y))
        self.has_targets = len(self.targets) > 0

class Navigation(BattleshipSystem):
    """Represents the navigation system of the battleship."""
    NAME = "Navigation"
    ALLOWED_DISTANCE_ERROR = 50
    
    def setup(self, **kwargs):
        self.waypoints = []
        self.waypoint_distances = []
        self.completed_waypoints = []
        self.actual_path = []
        self.next_waypoint = None
        self.has_waypoints = False
        self.logging_variables = ["next_waypoint", "waypoints", "waypoint_distances", "completed_waypoints", "has_waypoints"]
        if "waypoints" in kwargs:
            for waypoint in kwargs["waypoints"]:
                self.add_waypoint(*waypoint)
    
    def update(self, timedelta):
        if len(self.waypoints) > 0:
            if SimulatorUtilities.is_point_within_circle(self.waypoints[0][0], self.waypoints[0][1], self.model.x, self.model.y, self.ALLOWED_DISTANCE_ERROR):
                self.completed_waypoints.append(self.waypoints.pop(0))
                if len(self.waypoints) > 0:
                    self.next_waypoint = self.waypoints[0]
                else:
                    self.next_waypoint = None
            # Get the distances
            if len(self.waypoints) > 0:
                self.waypoint_distances = [SimulatorUtilities.distance(waypoint, (self.model.x, self.model.y)) for waypoint in self.waypoints]
            else:
                self.waypoint_distances = []
        self.has_waypoints = len(self.waypoints) > 0
        self.actual_path.append((self.model.x, self.model.y))

    def commands(self):
        return ["ADD_WAYPOINT"]

    def handle_command(self, command, *args):
        match command:
            case "ADD_WAYPOINT":
                self.add_waypoint(*args)
            case _:
                print(f"Unrecognized command: {command}")

    def add_waypoint(self, x, y):
        self.waypoints.append((x, y))
        if len(self.waypoints) > 0 and self.next_waypoint is None:
            self.next_waypoint = self.waypoints[0]
        self.has_waypoints = len(self.waypoints) > 0

class RadarSonar(BattleshipSystem):
    """Represents the radar/sonar system of the battleship."""
    NAME = "RadarSonar"
    
    def setup(self, **kwargs):
        # This is the world as it is known to the radar/sonar
        self.chart = [] if self.model.world is None else self.model.get_attribute("World:obstacles")
        # These are objects that the system identifies
        self.objects = []
        self.radar_objects = []
        self.radar_object_distances = []
        self.warning_objects = []
        self.warning_object_distances = []
        self.collision_objects = []
        self.logging_variables = ["collision_warning", "collision_event", "radar_geometry", "radar_objects", "radar_object_distances", "warning_objects", "radar_object_distances", "collision_objects", "transformed_geometry"]
        #self.transformed_geometry = SimulatorUtilities.transform_coordinates(self.model.geometry, self.model.x, self.model.y, SimulatorUtilities.heading_to_angle(self.model.heading))
        self.transformed_geometry = SimulatorUtilities.transform_coordinates(self.model.geometry, self.model.x, self.model.y, self.model.heading)
        self.minimum_safe_distance = 100 if "minimum_safe_distance" not in kwargs else kwargs["minimum_safe_distance"]
        self.minimum_safe_area_geometry = self.calculate_min_safe_distance_area()
        self.radar_range = 1000 if "radar_range" not in kwargs else kwargs["radar_range"]
        self.radar_geometry = self.get_radar_geometry(self.model.x, self.model.y, self.radar_range)
        self.collision_warning = False
        self.collision_event = False
    
    def update(self, timedelta):
        # Identify collisions with the known world
        self.collision_warning = False
        self.collision_event = False
        #current_msa_geometry = SimulatorUtilities.transform_coordinates(self.minimum_safe_area_geometry, self.model.x, self.model.y, SimulatorUtilities.heading_to_angle(self.model.heading))
        #self.transformed_geometry = SimulatorUtilities.transform_coordinates(self.model.geometry, self.model.x, self.model.y, SimulatorUtilities.heading_to_angle(self.model.heading))
        current_msa_geometry = SimulatorUtilities.transform_coordinates(self.minimum_safe_area_geometry, self.model.x, self.model.y, self.model.heading)
        self.transformed_geometry = SimulatorUtilities.transform_coordinates(self.model.geometry, self.model.x, self.model.y, self.model.heading)
        self.radar_geometry = self.get_radar_geometry(self.model.x, self.model.y, self.radar_range)
        object_names = [k for k,m in self.get_attribute("World:models").items() if m is not self.model]
        self.objects = [self.get_attribute(f"World:{n}:RadarSonar:transformed_geometry") for n in object_names]
        self.radar_objects = []
        self.radar_object_distances = []
        self.warning_objects = []
        self.warning_object_distances = []
        self.collision_objects = []
        for world_object in self.chart + self.objects:
            in_radar_range, intersecting_shapes = SimulatorUtilities.polygons_intersect(self.radar_geometry, world_object)
            if in_radar_range:
                for intersecting_shape in intersecting_shapes:
                    self.radar_objects.append(intersecting_shape)
                    # Get the distances
                    self.radar_object_distances.append([SimulatorUtilities.distance(c, (self.model.x, self.model.y)) for c in intersecting_shape])

            in_msa_range, intersecting_shapes = SimulatorUtilities.polygons_intersect(current_msa_geometry, world_object)
            if in_msa_range:
                self.collision_warning = True
                for intersecting_shape in intersecting_shapes:
                    self.warning_objects.append(intersecting_shape)
                    # Get the distances
                    self.warning_object_distances.append([SimulatorUtilities.distance(c, (self.model.x, self.model.y)) for c in intersecting_shape])
                if SimulatorUtilities.polygons_intersect(self.transformed_geometry, world_object)[0]:
                    self.collision_event = True
                    self.collision_objects.append(world_object)
    
    def commands(self):
        return ["TOGGLE"]

    def handle_command(self, command, *args):
        match command:
            case "TOGGLE":
                self.toggle(*args)
            case _:
                print(f"Unrecognized command: {command}")
    
    def calculate_min_safe_distance_area(self):
        return SimulatorUtilities.buffer_shape(self.model.geometry, self.minimum_safe_distance)

    def get_radar_geometry(self, x, y, r):
        return list(Point(x, y).buffer(r, resolution = 15).exterior.coords)