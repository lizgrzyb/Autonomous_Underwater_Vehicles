import arcade
import time

class WeaponsSystem(arcade.Window):
    def __init__(self):
        super().__init__(width=800, height=600, title="Weapons System", resizable=True)
        self.status = "Idle"
        self.time_elapsed = 0
        self.arming_time = 3
        self.firing_time = 3
        self.action_in_progress = False

    def setup(self):
        # Initialize any variables or states
        pass

    def on_draw(self):
        arcade.start_render()

        # Draw background
        arcade.draw_lrtb_rectangle_filled(0, self.width, self.height, 0, arcade.color.LIGHT_GRAY)

        # Button layout adjustments based on window size
        button_width = 180
        button_height = 50
        spacing = 20
        center_x = self.width // 2

        # Light Torpedo button
        if self.status == "Idle":
            arcade.draw_rectangle_filled(center_x - button_width, self.height // 2, button_width, button_height, arcade.color.BLACK)
        else:
            arcade.draw_rectangle_filled(center_x - button_width, self.height // 2, button_width, button_height, arcade.color.GRAY)
        arcade.draw_text("Light Torpedo", center_x - button_width - 50, self.height // 2 - 10, arcade.color.WHITE, 12)

        # Heavy Torpedo button
        if self.status == "Idle":
            arcade.draw_rectangle_filled(center_x + button_width, self.height // 2, button_width, button_height, arcade.color.BLACK)
        else:
            arcade.draw_rectangle_filled(center_x + button_width, self.height // 2, button_width, button_height, arcade.color.GRAY)
        arcade.draw_text("Heavy Torpedo", center_x + button_width - 50, self.height // 2 - 10, arcade.color.WHITE, 12)

        # Status
        arcade.draw_text(f"Status: {self.status}", center_x - 50, self.height // 2 + 70, arcade.color.BLACK, 14)

        # FIRE button (always visible)
        if self.status in ["Armed Light Torpedo", "Armed Heavy Torpedo"]:
            arcade.draw_rectangle_filled(center_x - button_width, self.height // 2 - button_height - spacing, button_width, button_height, arcade.color.BLACK)
            arcade.draw_text("FIRE", center_x - button_width - 50, self.height // 2 - button_height - spacing - 10, arcade.color.WHITE, 12)
        else:
            # Greyed out when not active
            arcade.draw_rectangle_filled(center_x - button_width, self.height // 2 - button_height - spacing, button_width, button_height, arcade.color.GRAY)
            arcade.draw_text("FIRE", center_x - button_width - 50, self.height // 2 - button_height - spacing - 10, arcade.color.WHITE, 12)

        # ABORT button (always visible)
        if self.status in ["Armed Light Torpedo", "Armed Heavy Torpedo"]:
            arcade.draw_rectangle_filled(center_x + button_width, self.height // 2 - button_height - spacing, button_width, button_height, arcade.color.BLACK)
            arcade.draw_text("ABORT", center_x + button_width - 50, self.height // 2 - button_height - spacing - 10, arcade.color.WHITE, 12)
        else:
            # Greyed out when not active
            arcade.draw_rectangle_filled(center_x + button_width, self.height // 2 - button_height - spacing, button_width, button_height, arcade.color.GRAY)
            arcade.draw_text("ABORT", center_x + button_width - 50, self.height // 2 - button_height - spacing - 10, arcade.color.WHITE, 12)


    def on_mouse_press(self, x, y, button, modifiers):
        # Check if any of the buttons were clicked
        center_x = self.width // 2
        button_width = 180
        button_height = 50
        spacing = 20

        if self.status == "Idle":
            if self._is_button_pressed(x, y, center_x - button_width, self.height // 2, button_width, button_height):  # Light Torpedo button
                self.status = "Arming Light Torpedo"
                self.time_elapsed = 0
                self.action_in_progress = True

            elif self._is_button_pressed(x, y, center_x + button_width + 5, self.height // 2, button_width, button_height):  # Heavy Torpedo button
                self.status = "Arming Heavy Torpedo"
                self.time_elapsed = 0
                self.action_in_progress = True

        elif self.status in ["Armed Light Torpedo", "Armed Heavy Torpedo"]:
            if self._is_button_pressed(x, y, center_x - button_width, self.height // 2 - button_height - spacing, button_width, button_height):  # FIRE button
                self.status = "Firing"
                self.time_elapsed = 0
                self.action_in_progress = True

            elif self._is_button_pressed(x, y, center_x + button_width + 5, self.height // 2 - button_height - spacing, button_width, button_height):  # ABORT button
                self.status = "Aborting"
                self.time_elapsed = 0
                self.action_in_progress = True

    def _is_button_pressed(self, x, y, button_x, button_y, button_width, button_height):
        # Check if the mouse click is within the button bounds
        return (button_x - button_width // 2 <= x <= button_x + button_width // 2 and
                button_y - button_height // 2 <= y <= button_y + button_height // 2)

    def update(self, delta_time):
        if self.action_in_progress:
            self.time_elapsed += delta_time

            if self.time_elapsed >= self.arming_time and self.status == "Arming Light Torpedo":
                self.status = "Armed Light Torpedo"
                self.time_elapsed = 0
                self.action_in_progress = False
            elif self.time_elapsed >= self.arming_time and self.status == "Arming Heavy Torpedo":
                self.status = "Armed Heavy Torpedo"
                self.time_elapsed = 0
                self.action_in_progress = False
            elif self.time_elapsed >= self.firing_time and self.status == "Firing":
                self.status = "Idle"
                self.time_elapsed = 0
                self.action_in_progress = False
            elif self.time_elapsed >= self.firing_time and self.status == "Aborting":
                self.status = "Idle"
                self.time_elapsed = 0
                self.action_in_progress = False