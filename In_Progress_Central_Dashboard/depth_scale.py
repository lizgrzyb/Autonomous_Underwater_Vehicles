import arcade
import random
import time

class DepthMonitor(arcade.Window):
    def __init__(self):
        # Dimensions of the depth monitor
        super().__init__(300, 500, "Depth Monitor", resizable=True)
        self.depth = 0  # Initial depth
        self.target_depth = 0  # Target depth
        self.depth_speed = 0  # Speed of depth change
        self.last_update_time = time.time()  # Time for updating depth
        
        # Parameters for the scale
        self.scale_width = 10
        self.scale_height = 580
        self.scale_x = 80
        self.scale_y = 10

    def setup(self):
        pass

    def update(self, delta_time):
        # Update depth every 0.5 seconds
        if time.time() - self.last_update_time >= 0.2:
            # Smoothly change the depth
            self.target_depth = random.randint(0, 1000)  # Set new target depth
            self.depth_speed = (self.target_depth - self.depth) * 0.01  # Smooth transition speed
            self.last_update_time = time.time()  # Reset the update timer
        
        # Update the current depth value
        self.depth += self.depth_speed

        # Clamp depth between 0 and 1000
        self.depth = max(0, min(1000, self.depth))

    def on_draw(self):
        arcade.start_render()
        
        # Draw the depth scale background (scale rectangle)
        arcade.draw_lrtb_rectangle_filled(self.scale_x, self.scale_x + self.scale_width, self.scale_y + self.scale_height, self.scale_y, arcade.color.LIGHT_GRAY)
        
        # Calculate the indicator height based on the current depth
        indicator_height = (self.depth / 1000) * self.scale_height  # Height based on depth value

        # Draw the depth indicator (a red bar for the current depth)
        # Ensure bottom is always less than or equal to top
        indicator_bottom = self.scale_y + self.scale_height - indicator_height
        indicator_top = self.scale_y + self.scale_height

        # Draw the BLUE indicator bar
        arcade.draw_lrtb_rectangle_filled(self.scale_x, self.scale_x + self.scale_width, indicator_top, indicator_bottom, arcade.color.BLUE)
        
        # Draw the scale labels (0-1000 depth scale)
        for i in range(0, 1100, 100):
            label_y = self.scale_y + self.scale_height - (i / 1000) * self.scale_height
            arcade.draw_text(f"{i}", self.scale_x + self.scale_width + 10, label_y, arcade.color.WHITE, 10)
            
         # Display the current depth at the bottom of the scale
        arcade.draw_text(f"Depth: {int(self.depth)}", self.scale_x + self.scale_width - 20, self.scale_y - 50, arcade.color.WHITE, 12)

    def on_resize(self, width, height):
        # Recalculate scale position if the window size changes
        # self.scale_x = width - 200  # Keep the scale at a fixed position on the right
        self.scale_y = height // 4  # Place the scale at the top portion of the window

