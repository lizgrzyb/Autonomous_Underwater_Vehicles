import BattleshipSimulator.Models.SimulatorUtilities as Utilities
import math

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

def test_headings():
    assert calculate_heading_from_points(0,0,0,1) == 0       # True north
    assert calculate_heading_from_points(0,0,1,1) == 45      # True northeast
    assert calculate_heading_from_points(0,0,1,0) == 90      # True east
    assert calculate_heading_from_points(0,0,1,-1) == 135    # Trie southeast
    assert calculate_heading_from_points(0,0,0,-1) == 180    # True south
    assert calculate_heading_from_points(0,0,-1,-1) == 225   # True southwest
    assert calculate_heading_from_points(0,0,-1,0) == 270    # True west
    assert calculate_heading_from_points(0,0,-1,1) == 315    # True northwest

def test_heading_conversions():
    assert heading_to_angle(0) == 90                         # North (positive) -> positive y-axis
    assert heading_to_angle(-360) == 90                      # North (negative) -> positive y-axis
    assert heading_to_angle(90) == 0                         # East (positive)  -> positive x-axis
    assert heading_to_angle(-270) == 0                       # East (negative)  -> positive x-axis
    assert heading_to_angle(180) == 270                      # South (positive) -> negative y-axis
    assert heading_to_angle(-180) == 270                     # South (negative) -> negative y-axis
    assert heading_to_angle(270) == 180                      # West (positive)  -> negative x-axis
    assert heading_to_angle(-90) == 180                      # West (negative)  -> negative x-axis

def test_turn_options():
    assert calculate_turn_options(0,0) == (0,0)              # From North -> North (no turn in either direction)
    assert calculate_turn_options(0, 90) == (-270,90)        # From North -> East  (three-quarter turn port or one-quarter turn starboard)
    assert calculate_turn_options(0, 180) == (-180,180)      # From North -> South (half turn port in either direction)
    assert calculate_turn_options(0, 270) == (-90,270)       # From North -> West  (one-quarter turn port or three-quarter turn starboard)
    assert calculate_turn_options(90, 89) == (-1,359)