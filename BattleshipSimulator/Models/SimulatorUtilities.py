import math
import numpy as np
import yaml
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.affinity import translate, rotate, scale
from BattleshipSimulator.python_vehicle_simulator.lib.gnc import attitudeEuler
from BattleshipSimulator.python_vehicle_simulator.vehicles import frigate
import os

def calculate_heading_from_points(object_x, object_y, direction_x, direction_y):
    # Calculate the difference in coordinates
    dx = direction_x - object_x
    dy = direction_y - object_y
    # Calculate the angle in radians between the positive x-axis and the line
    # from (object_x, object_y) to (direction_x, direction_y), and convert it to degrees
    angle_radians = math.atan2(dy, dx)
    angle_degrees = math.degrees(angle_radians)
    # Convert the angle from "mathematical" to "navigational" convention
    heading = (450 - angle_degrees) % 360
    # In navigational convention, North is 0 degrees
    if heading == 360:
        heading = 0
    return heading

def heading_to_angle(navigational_heading):
    # Convert navigational heading to mathematical angle in degrees
    # In navigational headings, degrees increase clockwise, with 0 degrees being North.
    # In mathematical angles, degrees increase counterclockwise, with 0 degrees being the positive x-axis (East).
    mathematical_angle = (450 - navigational_heading) % 360
    if mathematical_angle == 360:
        mathematical_angle = 0  # Normalize 360 to 0
    return mathematical_angle

def angle_to_heading(mathematical_angle):
    # This will likely never be used, because the Model will always work in heading,
    # and the View will need to translate it into the mathematical angle for drawing
    # but the Model should never need to take a mathematical angle and convert it the other way

    # Convert mathematical angle to navigational heading in degrees
    # In mathematical angles, degrees increase counterclockwise, with 0 degrees being the positive x-axis (East).
    # In navigational headings, degrees increase clockwise, with 0 degrees being North.
    navigational_heading = (450 - mathematical_angle) % 360
    if navigational_heading == 360:
        navigational_heading = 0  # Normalize 360 to 0
    return navigational_heading

def calculate_turn_options(current_heading, desired_heading):
    # Calculate the difference in degrees between the current and desired headings
    angle_difference = (desired_heading - current_heading) % 360
    # Determine the port and starboard options
    port_option = angle_difference - 360 if angle_difference > 0 else angle_difference
    starboard_option = angle_difference if angle_difference >= 0 else angle_difference + 360
    return port_option, starboard_option

def smallest_distance(angle1, angle2):
    # Handle negative angles
    if angle1 < 0:
        angle1 += 360
    if angle2 < 0:
        angle2 += 360
    # Calculate the absolute difference between the angles
    absolute_difference = abs(angle1 - angle2)
    # Handle angles that span more than 360 degrees
    if absolute_difference > 360:
        absolute_difference = 360 - absolute_difference
    # Calculate the smallest distance
    smallest_distance = min(absolute_difference, 360 - absolute_difference)
    return smallest_distance

def is_within_threshold(angle1, angle2, threshold):
    """
    Checks if angle1 is within a specified number of degrees (threshold) of angle2,
    considering the cyclic nature of angles.

    Args:
    angle1 (float): The first angle in degrees.
    angle2 (float): The second angle in degrees.
    threshold (float): The threshold in degrees.

    Returns:
    bool: True if angle1 is within the threshold degrees of angle2, False otherwise.
    """
    # Normalize angles to be within 0 to 360 degrees
    angle1 = angle1 % 360
    angle2 = angle2 % 360

    # Calculate the absolute difference
    diff = abs(angle1 - angle2)

    # Check the direct difference and the wrapped-around difference
    return diff <= threshold or diff >= 360 - threshold

def invert_heading(heading):
    """
    Convert a negative heading to a positive one and vice versa.
    
    If the heading is negative, it will be converted to a positive heading.
    If the heading is positive, it will be converted to a negative heading.
    Assumes heading is provided in degrees.
    """
    if heading < 0:
        # Convert negative heading to positive
        return heading + 360
    elif heading > 0:
        # Convert positive heading to negative
        return heading - 360
    else:
        # If the heading is 0, it is already at the neutral point
        return heading

def R2D(value):  # radians to degrees
    return value * 180 / math.pi

def calculate_angle_degrees(x1, y1, x2, y2):
    """
    Calculate the angle (in degrees) between two coordinates.

    Parameters:
    -----------
    x1 : float
        X-coordinate of the first point.
    y1 : float
        Y-coordinate of the first point.
    x2 : float
        X-coordinate of the second point.
    y2 : float
        Y-coordinate of the second point.
    
    Returns:
    --------
    angle_degrees : float
        The angle (in degrees) between the two coordinates.
    """
    # Calculate the difference in X and Y coordinates
    delta_x = x2 - x1
    delta_y = y2 - y1

    if delta_x == 0:
        return 0

    # Use atan2 to calculate the angle in radians
    """angle_radians = math.atan2(delta_x, delta_y)

    if (delta_x > 0 and delta_y > 0):
        # Convert radians to degrees
        angle_degrees = (math.degrees(angle_radians))
    elif (delta_x > 0 and delta_y < 0):
        # Convert radians to degrees
        angle_degrees = 180-(math.degrees(angle_radians))
    elif (delta_y > 0):
        # Convert radians to degrees
        angle_degrees = -(math.degrees(angle_radians))
    else:
        # Convert radians to degrees
        angle_degrees = -180+(math.degrees(angle_radians))"""
    
    # Use atan2 to calculate the angle in radians
    angle_radians = math.atan2(delta_y, delta_x)
 
    # if (delta_x > 0 and delta_y > 0):
    #     # Convert radians to degrees
    #     angle_degrees = 90-(math.degrees(angle_radians))
    # elif (delta_x > 0 and delta_y < 0):
    #     # Convert radians to degrees
    #     angle_degrees = 90+(math.degrees(angle_radians))
    # elif (delta_y > 0):
    #     # Convert radians to degrees
    #     angle_degrees = -(90-(math.degrees(angle_radians)))
    # else:
    #     # Convert radians to degrees
    #     angle_degrees = -(90+(math.degrees(angle_radians)))

    return R2D(angle_radians)

def calculate_rotation_angles(current_heading, desired_heading):
    # Normalize the headings to be within [0, 360)
    if (current_heading < 0):
        norm_cur_heading = 360 + current_heading
    else:
        norm_cur_heading = current_heading
    if (desired_heading < 0):
        norm_des_heading = 360 + desired_heading
    else:
        norm_des_heading = desired_heading
    if (norm_cur_heading >= norm_des_heading):
        angle_right =  abs(norm_cur_heading - norm_des_heading)
        angle_left = 360-angle_right
    else:
        angle_left =  abs(norm_cur_heading - norm_des_heading)
        angle_right = 360-angle_left


    # current_heading = current_heading
    # desired_heading = desired_heading
    
    # # Calculate the angles for left (counter-clockwise) and right (clockwise) rotations
    # angle_left = (desired_heading - current_heading) % 180
    # angle_right = (current_heading - current_heading) % 180
    
    return angle_left, angle_right

def update_circle_coordinates(current_x, current_y, center_x, center_y, radius, speed, timedelta):
    """
    Update the current x, y coordinates around a circle and return the angle in degrees.

    Parameters:
    -----------
    current_x : float
        Current X-coordinate.
    current_y : float
        Current Y-coordinate.
    center_x : float
        X-coordinate of the center of the circle.
    center_y : float
        Y-coordinate of the center of the circle.
    radius : float
        Radius of the circle.
    speed : float
        Speed of movement in pixels per second.
    timedelta : float
        Time duration since the last update (in seconds).

    Returns:
    --------
    new_x : float
        New X-coordinate after the update.
    new_y : float
        New Y-coordinate after the update.
    facing_angle_degrees : float
        Angle (in degrees) that the battleship is facing.
    """
    # Calculate the angular speed in radians per second
    angular_speed = speed / radius

    # Calculate the change in angle based on elapsed time
    delta_angle = angular_speed * timedelta

    # Calculate the new angle
    current_angle = math.atan2(current_y - center_y, current_x - center_x)
    new_angle = current_angle + delta_angle

    # Calculate the new coordinates
    new_x = center_x + radius * math.cos(new_angle)
    new_y = center_y + radius * math.sin(new_angle)

    # Convert the facing angle to degrees
    facing_angle_degrees = math.degrees(new_angle)

    return new_x, new_y, facing_angle_degrees % 360

def update_position(old_x, old_y, new_x, new_y, speed, time_delta):
    # Calculate the angle of movement
    dx = new_x - old_x
    dy = new_y - old_y
    angle = math.atan2(dy, dx)
    
    # Calculate the new position
    new_x = old_x + speed * time_delta * math.cos(angle)
    new_y = old_y + speed * time_delta * math.sin(angle)
    
    return new_x, new_y

def is_point_within_circle(x1, y1, x2, y2, radius=50):
    #x1,y1 is the center of the circle
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance <= radius

def calculate_line_coordinates_from_center(x, y, height, angle):
    """
    Calculate the start and end coordinates of a line.

    :param x: X-coordinate of the center of the line
    :param y: Y-coordinate of the center of the line
    :param height: The height (length) of the line
    :param angle: The angle (in degrees) of the line
    :return: A tuple containing the start and end coordinates ((x_start, y_start), (x_end, y_end))
    """
    angle_rad = math.radians(angle)
    dx = math.cos(angle_rad) * height / 2
    dy = math.sin(angle_rad) * height / 2
    x_start, y_start = x - dx, y - dy
    x_end, y_end = x + dx, y + dy
    return x_start, y_start, x_end, y_end

def calculate_line_coordinates_from_end(start_x, start_y, length, angle):
    """
    Calculate the end coordinates of a line given the start coordinates, length, and angle.

    :param start_x: X-coordinate of the start of the line
    :param start_y: Y-coordinate of the start of the line
    :param length: The length of the line
    :param angle: The angle (in degrees) of the line in heading format
    :return: A tuple containing the end coordinates (x_end, y_end)
    """
    angle_rad = math.radians(angle)
    # Calculate the change in x and y
    dx = length * math.cos(angle_rad)
    dy = length * math.sin(angle_rad)
    # Calculate the end coordinates
    x_end, y_end = start_x + dx, start_y + dy
    return start_x, start_y, x_end, y_end

def update_path_coordinates_with_angle(x, y, path, speed, timedelta):
    """
    Update the current x, y coordinates along a defined path based on a given speed and time delta.
    
    Parameters:
    -----------
    path : list of tuple
        A list of (x, y) coordinates defining the path.
    speed : float
        Speed of movement in units per second.
    timedelta : float
        Time duration since the last update (in seconds).
        
    Returns:
    --------gnc
        New Y-coordinate after the update.
    facing_angle_degrees : float
        Angle (in degrees) that the object is facing.
    updated_path : list of tuple or empty list
        Updated path starting from the new position or an empty list if the object reaches the end of the path.
    """

    # Calculate the distance to be covered in this timestep
    distance_to_cover = speed * timedelta
    
    # Extract the current position and the next waypoint
    current_pos = (x, y)
    next_waypoint = path[1]
    
    # Calculate the distance to the next waypoint
    distance_to_next_waypoint = math.sqrt((next_waypoint[0] - current_pos[0])**2 + 
                                        (next_waypoint[1] - current_pos[1])**2)
    
    # Determine the direction vector (normalized) to the next waypoint
    dx = (next_waypoint[0] - current_pos[0]) / distance_to_next_waypoint
    dy = (next_waypoint[1] - current_pos[1]) / distance_to_next_waypoint
    
    # Calculate the facing angle
    facing_angle_rad = math.atan2(dy, dx)
    facing_angle_degrees = (math.degrees(facing_angle_rad) + 270) % 360
    
    while distance_to_cover > distance_to_next_waypoint and len(path) > 2:
        # Subtract the distance to the next waypoint from the total distance to cover
        # distance_to_cover -= distance_to_next_wagnc
        
        # Calculate the distance to the next waypoint
        distance_to_next_waypoint = math.sqrt((next_waypoint[0] - current_pos[0])**2 + 
                                            (next_waypoint[1] - current_pos[1])**2)
        
        # Determine the direction vector (normalized) to the next waypoint
        dx = (next_waypoint[0] - current_pos[0]) / distance_to_next_waypoint
        dy = (next_waypoint[1] - current_pos[1]) / distance_to_next_waypoint
    
    if len(path) <= 2 and distance_to_cover >= distance_to_next_waypoint:
        # If the object reaches the end of the path or exceeds the path length
        return current_pos[0], current_pos[1], facing_angle_degrees, []
    
    # Update the current position based on the remaining distance to cover
    new_x = current_pos[0] + dx * distance_to_cover
    new_y = current_pos[1] + dy * distance_to_cover
    
    # Update the path to start from the new position
    #updated_path = [(new_x, new_y)] + path[1:]
    updated_path = path
    
    return new_x, new_y, facing_angle_degrees, updated_path

def polygons_intersect(polygon1_coords, polygon2_coords):
    """
    Determine if one polygon touches or overlaps another polygon with optional transformations.

    Parameters:
    -----------
    polygon1_coords : list of tuple
        A list of (x, y) tuples defining the first polygon.
    polygon2_coords : list of tuple
        A list of (x, y) tuples defining the second polygon.
    offset1 : tuple, optional
        An (x, y) tuple defining the offset for the first polygon.
    offset2 : tuple, optional
        An (x, y) tuple defining the offset for the second polygon.
    angle1 : float, optional
        Rotation angle in degrees for the first polygon.
    angle2 : float, optional
        Rotation angle in degrees for the second polygon.

    Returns:
    --------
    bool
        True if the polygons touch or overlap after transformations, otherwise False.
    """

    # Convert coordinates to Shapely Polygons
    polygon1 = Polygon(polygon1_coords)
    polygon2 = Polygon(polygon2_coords)
    # Check if the polygons intersect (touch or overlap)
    intersection = polygon1.intersection(polygon2)
    is_overlap = not intersection.is_empty

    # Convert to a list of Polygons (to handle MultiPolygon instances)
    if isinstance(intersection, MultiPolygon):
        intersection = list(intersection.geoms)
    else:
        intersection = [intersection]
    
    return is_overlap, [list(i.exterior.coords) for i in intersection] if is_overlap else None

def line_intersects_polygon(line_coords, polygon_coords):
    """
    Determine if a line (defined by two points) intersects a polygon.

    Parameters:
    -----------
    line_coords : list of tuple
        A list of two (x, y) tuples defining the line.
    polygon_coords : list of tuple
        A list of (x, y) tuples defining the polygon.

    Returns:
    --------
    bool
        True if the line intersects (touches or crosses) the polygon, otherwise False.
    """

    # Convert coordinates to Shapely LineString and Polygon
    line = LineString(line_coords)
    polygon = Polygon(polygon_coords)

    # Check if the line intersects the polygon
    is_intersect = line.intersects(polygon)

    return is_intersect

def calculate_relative_angles(x, y, heading, polygon_coords):
    """
    Calculate relative angles to each point in a polygon from an object's position and heading.

    Parameters:
    - x (float): x-coordinate of the object.
    - y (float): y-coordinate of the object.
    - heading (float): Heading angle of the object in degrees.
    - polygon_coords (list of tuple): List of (x, y) coordinates of the polygon.

    Returns:
    - list: List of relative angles to each point in the polygon.
    """
    relative_angles = []

    for px, py in polygon_coords:
        # Angle from object to polygon point
        angle_to_point = math.degrees(math.atan2(py - y, px - x)) % 360

        # Relative angle considering the object's heading
        relative_angle = (angle_to_point - heading) % 360

        # Adjust for angles greater than 180 degrees
        if relative_angle > 180:
            relative_angle -= 360

        relative_angles.append(relative_angle)

    return relative_angles

def transform_coordinates(coords, dx=0, dy=0, rotation_deg=0, scaling_factor=1.0, origin='center'):
    """
    Apply transformations to a set of coordinates, with optional absolute pixel scaling.

    Parameters:
    - coords (list of tuple): List of (x, y) coordinates.
    - dx (float): Translation in x-direction.
    - dy (float): Translation in y-direction.
    - rotation_deg (float): Rotation angle in degrees.
    - scaling_factor (float): Factor by which to scale the shape. Default is 1.0 (no scaling).
    - scale_pixels (float): Number of pixels by which to scale the shape. Overrides scaling_factor.
    - origin (str or tuple): The point around which rotation and scaling will be performed.

    Returns:
    - list of tuple: Transformed coordinates.
    """
    polygon = Polygon(coords)

    # Translate
    polygon = translate(polygon, xoff=dx, yoff=dy)

    # Rotate
    polygon = rotate(polygon, angle=rotation_deg, origin=origin)

    # Scale   
    polygon = scale(polygon, xfact=scaling_factor, yfact=scaling_factor, origin=origin)

    return list(polygon.exterior.coords)

def buffer_shape(geometry, distance):
    """
    Expand a convex polygon in all directions using the Minkowski sum concept.
    
    The function leverages the `buffer` method from the Shapely library, which computes 
    the Minkowski sum of the input polygon and a disk of a given radius. This results in 
    expanding the polygon uniformly in every direction by the specified distance.

    Parameters
    ----------
    vertices : list of tuple
        A list of (x, y) tuples defining the convex polygon.
    distance : float, optional
        The distance to expand the polygon in all directions. Default is 100.

    Returns
    -------
    list of tuple
        A list of (x, y) vertices of the expanded polygon. The last point is not repeated.
    """
    
    # Create a shapely polygon from the vertices
    polygon = Polygon(geometry)
    # Use buffer to expand the polygon
    expanded_polygon = polygon.buffer(distance)
    return list(expanded_polygon.exterior.coords)

def get_origin_transform(min_x, max_x, min_y, max_y):
    # Calculate the midpoints of the shape's bounding box
    midpoint_x = (max_x + min_x) / 2.0
    midpoint_y = (max_y + min_y) / 2.0
    
    # Calculate the translation required to move the midpoint to (0,0)
    translate_x = -midpoint_x
    translate_y = -midpoint_y
    
    # Return the new bounding box coordinates
    return translate_x, translate_y

def distance(point1, point2):
    """
    Calculate the Euclidean distance between two points in 2D.

    Args:
    point1 (tuple): A tuple representing the first point (x1, y1).
    point2 (tuple): A tuple representing the second point (x2, y2).

    Returns:
    float: The Euclidean distance between the two points.
    """
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def getNextPosition(speed, targetHeading, prevEta, vehicle, timeDelta, oldNu, oldU):
    #################################################################
    # prevEta, oldNu, oldU determine the state of the               #
    # vehicle in the past                                           #
    # targetHeading is the new heading the ship wants to go         #
    # speed is the current speed                                    #
    # timeDelta is the change in time to the next index in simData  #
    #################################################################
    # u is control

    vehicle.ref = targetHeading           # set the vehicles autopilot to target the heading
    DOF = 6                     # degrees of freedom
    # Initial state vectors
    eta = prevEta    # position/attitude, user editable
    nu = oldNu                              # velocity, defined by vehicle class
    u_actual = oldU                  # actual inputs, defined by vehicle class - steering?
    # Initialization of table used to store the simulation data
    simData = np.empty( [0, 2*DOF + 2 * vehicle.dimU], float)
    # Vehicle specific control systems
    if (vehicle.controlMode == 'depthAutopilot'):
        u_control = vehicle.depthAutopilot(eta,nu,timeDelta)
    elif (vehicle.controlMode == 'headingAutopilot'):
        u_control = vehicle.headingAutopilot(eta,nu,timeDelta)   
    elif (vehicle.controlMode == 'depthHeadingAutopilot'):
        u_control = vehicle.depthHeadingAutopilot(eta,nu,timeDelta)             
    elif (vehicle.controlMode == 'DPcontrol'):
        u_control = vehicle.DPcontrol(eta,nu,timeDelta)

    # Store simulation data in simData
    # States, inc. heading, rudder, position, etc.
    signals = np.append( np.append( np.append(eta,nu),u_control), u_actual )
    # Refactored signals in the correct format
    simData = np.vstack( [simData, signals] )

    # Propagate vehicle and attitude dynamics
    nu, u_actual = vehicle.dynamics(eta,nu,u_actual,u_control,timeDelta)
    eta = attitudeEuler(eta,nu,timeDelta)

    return simData, eta, nu, u_actual

def load_yaml(infile):
    with open(infile, "r") as stream:
        return yaml.safe_load(stream)

def get_filename_without_extension(file_path):
    """
    Extracts the filename without the extension from a given file path.

    Args:
    file_path (str): The full path of the file.

    Returns:
    str: The filename without its extension.
    """
    # Extract the base name (e.g., "example.txt" from "/path/to/example.txt")
    base_name = os.path.basename(file_path)

    # Split the base name by the dot and discard the extension
    file_name_without_extension = os.path.splitext(base_name)[0]

    return file_name_without_extension