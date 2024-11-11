import requests
from BattleshipSimulator.Models.GetterSetter import GetterSetter
import BattleshipSimulator.Models.SimulatorUtilities as SimulatorUtilities
import shapely
import csv

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

class BaseRemoteNavigator(BaseNavigator):

    def __init__(self, model, url = "http://localhost", timeout = .25, attributes = ["x", "y", "heading"]):
        super().__init__(model)
        self.timeout = timeout
        self.logging_variables += ["is_error", "error_text"]
        self.POST_url = url
        self.attributes = attributes
        self.is_error = False
        self.error_text = ""
    
    def override(self):
        return self.send_post_request()
    
    def send_post_request(self):
        """
        Send a POST request to the specified URL with the given data.
        
        Returns:
        - dict: The parsed JSON data from the response.
        """
        self.is_error = False
        self.error_text = ""

        try:
            return requests.post(self.POST_url, timeout = self.timeout, json = {k:self.model.get_attribute(k.replace(".",":")) for k in self.attributes}).json()
        except Exception as err:
            self.is_error = True
            self.error_text = str(err)
            return {}


######################################################################
#   Get the bounding box of a set of coordinates.                    #
#                                                                    #
#     Parameters:                                                    #
#     - None                                                         #
#                                                                    #
#     Returns:                                                       #
#     - None                                                         #
#                                                                    #
#     Description:                                                   #
#     - interfaces with model and retrieves the current x, y,        #
#     heading, and objects in sensor range. Then draws rectangles    #
#     on the right and left halves of the sensor range, if objects   #
#     are in the right half the ship turns left and vice versa       #
#                                                                    #
#     TODO:                                                          #
#     - Improve logic such that it can handle objects on both sides  #
#                                                                    #
######################################################################
class CollisionAvoidanceNavigator(BaseNavigator):
    
    def override(self):
        # Return true if any of the model's attributes were overridden
        if self.model.get_attribute("RadarSonar:collision_warning"):
            # boundary_dist = self.model.get_attribute("world:")
            boundary_dist = self.model.get_attribute("RadarSonar:radar_range")
            # buffer heading is the static variable used to determine the response to objects being detected
            buffer_heading = 50
            warning_objects = self.model.get_attribute("RadarSonar:warning_objects")
            heading = self.model.heading
            x0 = self.model.x
            y0 = self.model.y
            (x0,y0,x1,y1) = SimulatorUtilities.calculate_line_coordinates_from_end(x0,y0,boundary_dist,heading)
            width = self.model.get_attribute("RadarSonar:minimum_safe_distance")

            # coordinates for the ship side of the rectangles
            (min_x0, min_y0, max_x0, max_y0) = SimulatorUtilities.calculate_line_coordinates_from_center(x0,y0, width, heading+90)
            # coordinates for the radar range side of the rectangles
            (min_x1, min_y1, max_x1, max_y1) = SimulatorUtilities.calculate_line_coordinates_from_center(x1,y1, width, heading+90)

            #shapely rectangles
            poly1 = shapely.Polygon([(min_x0, min_y0), (min_x1, min_y1), (x1, y1), (x0, y0), (min_x0, min_y0)])
            poly2 = shapely.Polygon([(max_x0, max_y0), (max_x1, max_y1), (x1, y1), (x0, y0), (max_x0, max_y0)])
            collision = False
            sign = -1
            for object in warning_objects:
                # check for intersection of the polygons and warning objects
                if (shapely.intersects(shapely.Polygon(object), poly1) or shapely.intersects(shapely.Polygon(object), poly2)):
                    collision = True
                    if (shapely.intersects(shapely.Polygon(object), poly1)):
                        sign = 1
            return {"heading": heading + sign * buffer_heading} if collision else {}
        else:
            return {}

class PointAvoidanceNavigator(BaseNavigator):

    def __init__(self, model):
        super().__init__(model)
        self.logging_variables = ["relevant_objects"]
        self.relevant_objects = []
        self.last_override_value = None

    def override(self):
        if self.model.get_attribute("RadarSonar:collision_warning"):
            safe_threshhold = self.model.get_attribute("length") // 2
            line_distance = self.model.get_attribute("RadarSonar:minimum_safe_distance") + (self.model.get_attribute("length") // 2)
            # Figure out if there are any dangerous obstacles, in a line along current_heading extending through radar_range
            model_x = self.model.get_attribute("x")
            model_y = self.model.get_attribute("y")
            model_h = self.model.get_attribute("heading")
            model_chosen_h = self.model.get_attribute("chosen_heading")
            heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                model_x,
                model_y,
                line_distance,
                model_h
            )
            headling_line_coords = ((heading_line[0], heading_line[1]), (heading_line[2], heading_line[3]))
            chosen_heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                model_x,
                model_y,
                line_distance,
                model_chosen_h
            )
            chosen_heading_line_coords = ((chosen_heading_line[0], chosen_heading_line[1]), (chosen_heading_line[2], chosen_heading_line[3]))

            heading_override = False
            waypoint_heading_override = False
            self.relevant_objects = []
            for obstacle in self.model.get_attribute("RadarSonar:radar_objects"):
                # Artificially increase the size of the object by 2x the ship's width
                enlarged_obstacle = SimulatorUtilities.buffer_shape(obstacle, safe_threshhold)
                obstacle_added = False
                if SimulatorUtilities.line_intersects_polygon(headling_line_coords, enlarged_obstacle):
                    heading_override = True
                    # Save a reference to the enlarged obstacle, the distance to all of its points, and the angle in relation to the current heading
                    self.relevant_objects.append(enlarged_obstacle)
                    obstacle_added = True
                    # TODO: if x,y is already inside the polygon, skim along the edge
                if SimulatorUtilities.line_intersects_polygon(chosen_heading_line_coords, enlarged_obstacle):
                    waypoint_heading_override = True
                    # Save a reference to the enlarged obstacle, the distance to all of its points, and the angle in relation to the current heading
                    if not obstacle_added:
                        self.relevant_objects.append(enlarged_obstacle)
                    # TODO: if x,y is already inside the polygon, skim along the edge
            
            # Plot the minimum course to avoid the obstacles, starting from the current heading. Prefer to keep going in the same direction that it's already turning
            if heading_override or waypoint_heading_override:
                # Index 0 is the current heading, index 1 is the waypoint heading
                # In each list, index 0 is port, index 1 is starboard, index 2 is the index of the preferred direction
                min_angles = [[0,0,0],[0,0,0]]
                # If the current heading doesn't need an override, attempt to get as close to the waypoint heading as possible
                base_headings = [model_h, model_chosen_h]
                for i in range(2):
                    if (i == 0 and not heading_override) or (i == 1 and not waypoint_heading_override):
                        continue
                    base_heading = base_headings[i]
                    for obstacle in self.relevant_objects:
                        candidate_angles = SimulatorUtilities.calculate_relative_angles(model_x, model_y, base_heading, obstacle)
                        min_angles[i][0] = max(min_angles[i][0], max(candidate_angles))
                        min_angles[i][1] = min(min_angles[i][1], min(candidate_angles))
                    min_angles[i][2] = 0 if min_angles[i][0] <= abs(min_angles[i][1]) else 1
                # Get the best of the values
                best_port_angle = 0 if min_angles[0][0] < min_angles[1][0] else 1
                best_starboard_angle = 0 if min_angles[0][1] > min_angles[1][1] else 1
                chosen_direction = 0 if min_angles[best_port_angle][0] <= abs(min_angles[best_starboard_angle][1]) else 1

                new_heading = (base_headings[best_port_angle] + min_angles[best_port_angle][chosen_direction] + 1) if chosen_direction == 0 else (base_headings[best_starboard_angle] + min_angles[best_starboard_angle][chosen_direction] - 1)

                # Prevent the heading from swinging wildly to the other direction
                if self.last_override_value is not None:
                    if (self.last_override_value < 0 and new_heading > 0) or (self.last_override_value > 0 and new_heading < 0):
                        new_heading = SimulatorUtilities.invert_heading(new_heading)
                self.last_override_value = new_heading
                
                return {"heading": new_heading}
            else:
                self.last_override_value = None
                return {}
        else:
            self.last_override_value = None
            return {}
        

# CIP begin
class NewPointAvoidanceNavigator(BaseNavigator):

    def __init__(self, model):
        super().__init__(model)
        self.logging_variables = ["relevant_objects"]
        self.relevant_objects = []
        self.last_override_value = None

    def override(self):
        if self.model.get_attribute("RadarSonar:collision_warning"):
            safe_threshhold = self.model.get_attribute("length") // 2
            line_distance = self.model.get_attribute("RadarSonar:minimum_safe_distance") + (self.model.get_attribute("length") // 2)
            # Figure out if there are any dangerous obstacles, in a line along current_heading extending through radar_range
            model_x = self.model.get_attribute("x")
            model_y = self.model.get_attribute("y")
            model_h = self.model.get_attribute("heading")
            model_chosen_h = self.model.get_attribute("chosen_heading")
            heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                model_x,
                model_y,
                line_distance,
                model_h
            )
            headling_line_coords = ((heading_line[0], heading_line[1]), (heading_line[2], heading_line[3]))
            chosen_heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                model_x,
                model_y,
                line_distance,
                model_chosen_h
            )
            chosen_heading_line_coords = ((chosen_heading_line[0], chosen_heading_line[1]), (chosen_heading_line[2], chosen_heading_line[3]))

            heading_override = False
            waypoint_heading_override = False
            self.relevant_objects = []

            # try to generate sonar training data
            current_point = shapely.Point(model_x, model_y)
            collision_distance_in_each_angle = [model_x, model_y, model_chosen_h]
            for angle in range(0, 360, 1):
                min_collision_distance_in_angle = None
                for obstacle in self.model.get_attribute("RadarSonar:radar_objects"):
                    collision_distance_in_angle = SimulatorUtilities.get_distance_at_angle(current_point, shapely.Polygon(obstacle), angle)
                    if (collision_distance_in_angle == None):
                        continue
                    else:
                        if (min_collision_distance_in_angle == None):
                            min_collision_distance_in_angle = collision_distance_in_angle
                        else:
                            min_collision_distance_in_angle = min(min_collision_distance_in_angle, collision_distance_in_angle)
                
                collision_distance_in_each_angle.append(min_collision_distance_in_angle if min_collision_distance_in_angle is not None else 0)
            with open("collision_data.csv", "a") as f: 
                for data in collision_distance_in_each_angle:
                    f.write(str(data) + ",")
                f.write("\n")

            for obstacle in self.model.get_attribute("RadarSonar:radar_objects"):
                # Artificially increase the size of the object by 2x the ship's width
                enlarged_obstacle = SimulatorUtilities.buffer_shape(obstacle, safe_threshhold)
                obstacle_added = False
                if SimulatorUtilities.line_intersects_polygon(headling_line_coords, enlarged_obstacle):
                    heading_override = True
                    # Save a reference to the enlarged obstacle, the distance to all of its points, and the angle in relation to the current heading
                    self.relevant_objects.append(enlarged_obstacle)
                    obstacle_added = True
                    # TODO: if x,y is already inside the polygon, skim along the edge
                if SimulatorUtilities.line_intersects_polygon(chosen_heading_line_coords, enlarged_obstacle):
                    waypoint_heading_override = True
                    # Save a reference to the enlarged obstacle, the distance to all of its points, and the angle in relation to the current heading
                    if not obstacle_added:
                        self.relevant_objects.append(enlarged_obstacle)
                    # TODO: if x,y is already inside the polygon, skim along the edge
            
            # Plot the minimum course to avoid the obstacles, starting from the current heading. Prefer to keep going in the same direction that it's already turning
            if heading_override or waypoint_heading_override:
                # Index 0 is the current heading, index 1 is the waypoint heading
                # In each list, index 0 is port, index 1 is starboard, index 2 is the index of the preferred direction
                min_angles = [[0,0,0],[0,0,0]]
                # If the current heading doesn't need an override, attempt to get as close to the waypoint heading as possible
                base_headings = [model_h, model_chosen_h]
                for i in range(2):
                    if (i == 0 and not heading_override) or (i == 1 and not waypoint_heading_override):
                        continue
                    base_heading = base_headings[i]
                    for obstacle in self.relevant_objects:
                        candidate_angles = SimulatorUtilities.calculate_relative_angles(model_x, model_y, base_heading, obstacle)
                        min_angles[i][0] = max(min_angles[i][0], max(candidate_angles))
                        min_angles[i][1] = min(min_angles[i][1], min(candidate_angles))
                    min_angles[i][2] = 0 if min_angles[i][0] <= abs(min_angles[i][1]) else 1
                # Get the best of the values
                best_port_angle = 0 if min_angles[0][0] < min_angles[1][0] else 1
                best_starboard_angle = 0 if min_angles[0][1] > min_angles[1][1] else 1
                chosen_direction = 0 if min_angles[best_port_angle][0] <= abs(min_angles[best_starboard_angle][1]) else 1

                new_heading = (base_headings[best_port_angle] + min_angles[best_port_angle][chosen_direction] + 1) if chosen_direction == 0 else (base_headings[best_starboard_angle] + min_angles[best_starboard_angle][chosen_direction] - 1)

                # Prevent the heading from swinging wildly to the other direction
                if self.last_override_value is not None:
                    if (self.last_override_value < 0 and new_heading > 0) or (self.last_override_value > 0 and new_heading < 0):
                        new_heading = SimulatorUtilities.invert_heading(new_heading)
                self.last_override_value = new_heading
                
                return {"heading": new_heading}
            else:
                self.last_override_value = None
                return {}
        else:
            self.last_override_value = None
            return {}


class SubmarineNavigator(BaseNavigator):
 
    def __init__(self, model):
        super().__init__(model)
        self.logging_variables += ["collision_warning", "detected_threats"]
        self.detected_threats = []
        self.supervisor_override = False
 
    def override(self):
        if self.model.get_attribute("Sonar:collision_warning"):
            safe_threshhold = self.model.get_attribute("length") // 2
            line_distance = self.model.get_attribute("RadarSonar:minimum_safe_distance") + (self.model.get_attribute("length") // 2)
            # Figure out if there are any dangerous obstacles, in a line along current_heading extending through radar_range
            model_x = self.model.get_attribute("x")
            model_y = self.model.get_attribute("y")
            model_h = self.model.get_attribute("heading")
            model_chosen_h = self.model.get_attribute("chosen_heading")

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
# CIP end