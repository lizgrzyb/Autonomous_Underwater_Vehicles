import matplotlib.pyplot as plt

# Scaling the original coordinates to fit the screen width=800, height=600
# Adding more variation to the Y coordinates
scaled_ocean_floor_points = [
    [0, 200],   # Start of the profile, slope down
    [20, 240],  # Intermediate point
    [40, 280],  # Intermediate point
    [60, 300],  # Intermediate point
    [80, 320],  # Steep drop into the trench
    [100, 350],  # Intermediate point
    [120, 380],  # Intermediate point in the trench
    [140, 410],  # Intermediate point
    [160, 420],  # Bottom of the trench
    [180, 400],  # Intermediate point
    [200, 390],  # Intermediate point on the rise
    [220, 380],  # Intermediate point
    [240, 370],  # Slope up out of the trench
    [260, 350],  # Intermediate point
    [280, 340],  # Intermediate point on the rise
    [300, 330],  # Intermediate point
    [320, 310],  # Abyssal plain
    [340, 320],  # Intermediate point in the plain
    [360, 330],  # Intermediate point in the plain
    [380, 325],  # Intermediate point in the plain
    [400, 330],  # Slight rise in the abyssal plain
    [420, 335],  # Intermediate point
    [440, 340],  # Intermediate point in the plain
    [460, 345],  # Intermediate point
    [480, 350],  # Continuing the plain
    [500, 340],  # Intermediate point before the rise
    [520, 320],  # Intermediate point before the rise
    [540, 310],  # Intermediate point
    [560, 300],  # Begin rising
    [580, 290],  # Intermediate point on the rise
    [600, 280],  # Intermediate point on the rise
    [620, 270],  # Intermediate point
    [640, 250],  # Continental rise
    [660, 240],  # Intermediate point on the slope
    [680, 225],  # Intermediate point on the slope
    [700, 215],  # Intermediate point
    [720, 210],  # Steep slope up
    [740, 205],  # Intermediate point
    [760, 215],  # More variation
    [780, 230],  # Small rise
    [800, 220]   # End of the profile with variation
]

# Add points at the bottom (depth = 600) to "close" the ocean floor profile at the screen height
scaled_ocean_floor_points = [[0, 600]] + scaled_ocean_floor_points + [[800, 600]]

# Unzip the coordinates
scaled_ocean_floor_x, scaled_ocean_floor_y = zip(*scaled_ocean_floor_points)

# Create the plot
plt.figure(figsize=(8, 6))  # Adjusting the figure size for 800x600 screen

# Plot the ocean floor (continuous shape)
plt.fill(scaled_ocean_floor_x, scaled_ocean_floor_y, 'brown', alpha=0.7)

# Configure the plot to represent the ocean floor section for 800x600 screen
plt.title("Submarine Simulator: Ocean Floor Profile with More Variation (800x600)")
plt.xlabel("Distance (X Axis)")
plt.ylabel("Depth (Y Axis)")
plt.xlim(0, 800)
plt.ylim(0, 600)  # Ensure the screen height goes from 0 to 600
plt.gca().invert_yaxis()  # Invert the Y-axis to have depth increasing downwards
plt.grid(True)

# Display the plot
plt.show()
