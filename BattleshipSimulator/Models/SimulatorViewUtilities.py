from shapely.geometry import Polygon

def scale_polygon(vertices, scale_factor):
    """
    Scale a polygon by a specified factor.

    Parameters
    ----------
    vertices : list of tuple
        A list of (x, y) tuples defining the polygon.
    scale_factor : float
        The factor by which to scale the polygon.

    Returns
    -------
    list of tuple
        A list of (x, y) vertices of the scaled polygon.
    """

    # Calculate the centroid of the polygon for scaling
    centroid_x = sum(x for x, _ in vertices) / len(vertices)
    centroid_y = sum(y for _, y in vertices) / len(vertices)

    # Scale each vertex relative to the centroid
    scaled_vertices = [
        (centroid_x + scale_factor * (x - centroid_x),
         centroid_y + scale_factor * (y - centroid_y))
        for x, y in vertices
    ]

    return scaled_vertices

def seconds_to_hms(seconds):
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def convert_coords_meters_to_pixels(x, y, pixels_per_meter):
    return (x * pixels_per_meter, y * pixels_per_meter)

def convert_coords_pixels_to_meters(x, y, pixels_per_meter):
    return (x / pixels_per_meter, y / pixels_per_meter)

def convert_coords_list_meters_to_pixels(coords_list, pixels_per_meter):
    return [convert_coords_meters_to_pixels(coords[0], coords[1], pixels_per_meter) for coords in coords_list]

def convert_coords_list_pixels_to_meters(coords_list, pixels_per_meter):
    return [convert_coords_pixels_to_meters(coords[0], coords[1], pixels_per_meter) for coords in coords_list]

def get_bounding_box(coords):
    """
    Get the bounding box of a set of coordinates.

    Parameters:
    - coords (list of tuple): List of (x, y) coordinates.

    Returns:
    - tuple: (x, y, width, height) where (x, y) is the center point of the bounding box.
    """
    polygon = Polygon(coords)
    min_x, min_y, max_x, max_y = polygon.bounds
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    width = max_x - min_x
    height = max_y - min_y

    return center_x, center_y, width, height