import yaml
import random
import math
from shapely.geometry import Polygon, MultiPolygon

BASE = 500
 
def draw_random_shape(x_offset, y_offset):
    circ_approx = 8

    shape = random.choice(["circle", "square", "triangle"])

    if shape == "circle":
        r = random.randint(BASE // 10, BASE)
        points = []
        for index in range(circ_approx):
            points.append([r*math.cos((index*2*math.pi)/circ_approx)+x_offset,r*math.sin((index*2*math.pi)/circ_approx)+y_offset])
            r = random.randint(1,BASE)
        points.append(points[0])
        return points
    elif shape == "square":
        side_length = random.randint(1, BASE)
        return [[x_offset, y_offset], [x_offset+side_length, y_offset], [x_offset+side_length, y_offset+side_length], [x_offset, y_offset+side_length], [x_offset, y_offset]]
    elif shape == "triangle":
        base = random.randint(1, BASE)
        height = random.randint(1, BASE)
        return [[x_offset, y_offset], [x_offset+base, y_offset+height], [x_offset+base, y_offset], [x_offset, y_offset]]

def within_range(x1, y1, x2,y2):
    return abs(x1 - x2) < 120 and abs(y1-y2) < 120
def within_range_land(x1, y1, obstacles):
    for i in obstacles:
        if abs(x1 - i[0][0]) < 40 and abs(y1-i[0][1]) < 40:
            return True
    return False

def combine_intersecting_shapes(shape1_coords, shape2_coords):
    """
    Takes two sets of coordinates, checks if the corresponding shapes intersect,
    and returns the combined shape if they do.

    :param shape1_coords: List of (x, y) tuples for the first shape.
    :param shape2_coords: List of (x, y) tuples for the second shape.
    :return: A list of (x, y) tuples representing the combined shape, 
             or None if they don't intersect.
    """

    # Create polygons from the provided coordinates
    shape1 = Polygon(shape1_coords)
    shape2 = Polygon(shape2_coords)

    # Check if the shapes intersect
    if shape1.intersects(shape2):
        # If they intersect, get the combined shape
        combined_shape = shape1.union(shape2)

        # Function to convert coordinates to integers
        def to_integer_coords(coords):
            new_coords = [[int(x), int(y)] for x, y in coords]
            i = 1
            while i < len(new_coords):
                if new_coords[i] in new_coords[i+1:]:
                    del new_coords[i]
                else:
                    i += 1

        # Handle MultiPolygon results
        if isinstance(combined_shape, MultiPolygon):
            return None
        else:
            # Single Polygon result
            return to_integer_coords(combined_shape.exterior.coords)
    else:
        # Return None if they do not intersect
        return None

def generate_yaml(name, version_num, amount_of_obstacles, amount_of_waypoints):
    data = dict(
        entities=[],
        world=dict(
            guardrails=[[0,0],[5000,5000]],
            obstacles=[]
        ),
        success_conditions={
            'World:PrimaryBattleship:Navigation:has_waypoints':False
        },
        failure_conditions={
            'World:PrimaryBattleship:RadarSonar:collision_event':True,
            'World:PrimaryBattleship:out_of_bounds':True
        }
    )

    primary_battleship = {
        'x':random.randint(data["world"]["guardrails"][0][0], data["world"]["guardrails"][1][0]),
        'y':random.randint(data["world"]["guardrails"][0][0], data["world"]["guardrails"][1][0]),
        'speed':5,
        'heading':0,
        'supervisor':"CollisionAvoidanceNavigator",
        '_id':"PrimaryBattleship",
        '_configuration':"entity_configs/arleigh_burke.yaml",
        '_Navigation':dict(
            waypoints=[]
        ),
        '_Weapons':dict(
            targets=[]
        )
    }

    proposed_obstacles = []
    for i in range(amount_of_obstacles):
        x_offset = random.randint(data["world"]["guardrails"][0][0], data["world"]["guardrails"][1][0])
        y_offset = random.randint(data["world"]["guardrails"][0][0], data["world"]["guardrails"][1][0])
        while (within_range(x_offset, y_offset, primary_battleship["x"], primary_battleship["y"])):
            x_offset = random.randint(data["world"]["guardrails"][0][0], data["world"]["guardrails"][1][0])
            y_offset = random.randint(data["world"]["guardrails"][0][0], data["world"]["guardrails"][1][0])
        #data["world"]["obstacles"].append(draw_random_shape(x_offset, y_offset))
        proposed_obstacles.append(draw_random_shape(x_offset, y_offset))
    
    # Consolidate the shapes into one if they overlap
    while len(proposed_obstacles) > 0:
        current_shape = proposed_obstacles[0]
        i = 1
        while len(proposed_obstacles) > 1 and i < len(proposed_obstacles):
            if (new_shape := combine_intersecting_shapes(current_shape, proposed_obstacles[i])) is not None:
                current_shape = new_shape
                del proposed_obstacles[i]
            else:
                i += 1
        data["world"]["obstacles"].append(current_shape)
        del proposed_obstacles[0]
    
    x_min, x_max, y_min, y_max = data["world"]["guardrails"][0][0] + 1000, data["world"]["guardrails"][1][0] - 1000, data["world"]["guardrails"][0][1] + 1000, data["world"]["guardrails"][1][1] - 1000

    x_offset = primary_battleship["x"]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][0],data["world"]["guardrails"][1][0])
    y_offset = primary_battleship["y"]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][1],data["world"]["guardrails"][1][1])
    while within_range_land(x_offset, y_offset, data["world"]["obstacles"]) or (x_offset <= x_min or x_offset >= x_max) or (y_offset <= y_min or y_offset >= y_max):
        x_offset = primary_battleship["x"]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][0],data["world"]["guardrails"][1][0])
        y_offset = primary_battleship["y"]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][1],data["world"]["guardrails"][1][1])
    primary_battleship["_Navigation"]["waypoints"].append([x_offset, y_offset])

    for i in range(1, amount_of_waypoints):
        x_offset = primary_battleship["_Navigation"]["waypoints"][-1][0]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][0],data["world"]["guardrails"][1][0])
        y_offset = primary_battleship["_Navigation"]["waypoints"][-1][1]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][1],data["world"]["guardrails"][1][1])
        while within_range_land(x_offset, y_offset, data["world"]["obstacles"]) or (x_offset <= x_min or x_offset >= x_max) or (y_offset <= y_min or y_offset >= y_max):
            x_offset = primary_battleship["_Navigation"]["waypoints"][-1][0]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][0],data["world"]["guardrails"][1][0])
            y_offset = primary_battleship["_Navigation"]["waypoints"][-1][1]+random.choice((-1,1))*random.randint(data["world"]["guardrails"][0][1],data["world"]["guardrails"][1][1])
        primary_battleship["_Navigation"]["waypoints"].append([x_offset, y_offset])
    
    x_offset = primary_battleship["_Navigation"]["waypoints"][-1][0]+random.choice((-1,1))*random.randint(x_min,x_max)
    y_offset = primary_battleship["_Navigation"]["waypoints"][-1][1]+random.choice((-1,1))*random.randint(y_min,y_max)
    while not within_range_land(x_offset, y_offset, data["world"]["obstacles"]):
        x_offset = primary_battleship["_Navigation"]["waypoints"][-1][0]+random.choice((-1,1))*random.randint(x_min,x_max)
        y_offset = primary_battleship["_Navigation"]["waypoints"][-1][1]+random.choice((-1,1))*random.randint(y_min,y_max)
    primary_battleship["_Weapons"]["targets"].append([x_offset, y_offset])

    data["entities"].append(primary_battleship)

    with open('scenarios/scenario'+str(name)+'-'+str(version_num)+'.yaml', 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


print("--------------------------------------------------------------")
print("Hello, welcome to the terrain generator for the battleship sim")
print("--------------------------------------------------------------")
print("\n\n")

seed_in = input("Please enter a seed for the randomization: [65535] ")
seed_in = int(seed_in) if seed_in != "" else 65535
random.seed(seed_in)
amount_of_obstacles = input("Please enter the amount of obstacles for this set of terrain: [15] ")
amount_of_obstacles = int(amount_of_obstacles) if amount_of_obstacles != "" else 15
amount_of_waypoints = input("Please enter the amount of waypoints for this set of terrain: [3] ")
amount_of_waypoints = int(amount_of_waypoints) if amount_of_waypoints != "" else 3
name = input("Please enter an id for this scenario: [-gen] ")
name = name if name != "" else "-gen"
amount_of_versions = input("Please enter the amount of versions to generate with these parameters: [50] ")
amount_of_versions = int(amount_of_versions) if amount_of_versions != "" else 50

for i in range(amount_of_versions):
    generate_yaml(name, i, amount_of_obstacles, amount_of_waypoints)