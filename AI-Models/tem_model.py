import requests
from BattleshipSimulator.Models.GetterSetter import GetterSetter
import BattleshipSimulator.Models.SimulatorUtilities as SimulatorUtilities
import shapely
 
class BaseNavigator(GetterSetter):
 
    def __init__(self, model):
        self.model = model
        self.supervisor_override = False
        self.logging_variables = []
 
    def override(self):
        # Return true if any of the model's attributes were overridden
        return self.supervisor_override
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
 
class SubmarineNavigator(BaseNavigator):
 
    def __init__(self, model):
        super().__init__(model)
        self.logging_variables += ["collision_warning", "detected_threats"]
        self.detected_threats = []
        self.supervisor_override = False
 
    def override(self):
        if self.model.get_attribute("Sonar:collision_warning"):
            return self.avoid_collision()
        return {}
 
    def avoid_collision(self):
        # Collision avoidance logic based on sonar data
        boundary_dist = self.model.get_attribute("Sonar:range")
        buffer_heading = 30  # Adjust as per submarine agility
        detected_objects = self.model.get_attribute("Sonar:detected_objects")
        heading = self.model.heading
        pitch = self.model.pitch
        x0, y0, z0 = self.model.x, self.model.y, self.model.z
        (x1, y1, z1) = SimulatorUtilities.calculate_3d_line_coordinates(x0, y0, z0, boundary_dist, heading, pitch)
        width = self.model.get_attribute("Sonar:minimum_safe_distance")
 
        # Create 3D bounding volumes using shapely or similar library adapted for 3D
        poly1 = shapely.Polygon([(x0, y0), (x1, y1)])  # Simplified for 2D, adapt for 3D
        collision = False
        for obj in detected_objects:
            if shapely.intersects(shapely.Polygon(obj), poly1):
                collision = True
        if collision:
            # Change course, ascend/descend to avoid obstacles
            return {"heading": heading + buffer_heading, "pitch": pitch + 5}  # Example values
        return {}
 
class SubmarineWeaponsModule:
 
    def __init__(self):
        self.light_torpedo_count = 10
        self.heavy_torpedo_count = 5
 
    def select_weapon(self, target_size):
        # Decision tree logic for weapon selection
        if target_size < 5:  # Example size threshold
            return "Light Torpedo" if self.light_torpedo_count > 0 else "None"
        else:
            return "Heavy Torpedo" if self.heavy_torpedo_count > 0 else "None"
 
    def fire_weapon(self, weapon_type):
        if weapon_type == "Light Torpedo" and self.light_torpedo_count > 0:
            self.light_torpedo_count -= 1
            print("Fired Light Torpedo!")
        elif weapon_type == "Heavy Torpedo" and self.heavy_torpedo_count > 0:
            self.heavy_torpedo_count -= 1
            print("Fired Heavy Torpedo!")
        else:
            print("No ammunition left for", weapon_type)
 
class SubmarineNavigationWithWeapons(SubmarineNavigator):
 
    def __init__(self, model):
        super().__init__(model)
        self.weapons_module = SubmarineWeaponsModule()
 
    def override(self):
        # Perform base navigation override
        nav_override = super().override()
        if nav_override:
            # If collision avoidance is active, hold fire
            print("Holding fire due to navigation override.")
            return nav_override
        # Check for detected threats
        threat_level = self.model.get_attribute("Sonar:threat_level")
        target_size = self.model.get_attribute("Sonar:target_size")
        selected_weapon = self.weapons_module.select_weapon(target_size)
        if threat_level == "high" and selected_weapon != "None":
            print(f"Detected high threat. Preparing to fire {selected_weapon}.")
            self.weapons_module.fire_weapon(selected_weapon)
        else:
            print("No immediate threat or no available weapons.")
 
        return {}