import BattleshipSimulator.Models.SimulatorUtilities as SimulatorUtilities
import BattleshipSimulator.Models.SimulatorViewUtilities as SimulatorViewUtilities
import arcade

class BattleshipViewCLI():
    
    def __init__(self, controller):
        self.elapsed_time = 0
        self.controller = controller
    
    def start(self, timedelta = .5):
        print(f"Running {self.controller.get_attribute('Simulation:config_file')}")
        while self.controller.get_attribute("Simulation:simulation_running"):
            self.on_update(timedelta)
        print(f"  {('+' if self.controller.get_attribute('Simulation:simulation_status') == 'Success' else '-')} Simulation {('successful' if self.controller.get_attribute('Simulation:simulation_status') == 'Success' else 'failed')} in {self.elapsed_time} seconds")
    
    def on_update(self, timedelta):
        self.elapsed_time += timedelta
        # Update the model
        self.controller.update(timedelta)

class BattleshipViewGUI(arcade.View):
    """
    The GUI representation of the battleship simulation using the arcade library.

    Attributes:
    -----------
    controller : BattleshipController
        The controller to handle user interactions and update the model.
    screen_width : int
        The initial width of the screen.
    screen_height : int
        The initial height of the screen.

    Methods:
    --------
    on_draw():
        Draws the battleship's representation and information on the screen.
    on_key_press(key, _):
        Handles key press events, triggering appropriate actions.
    on_key_release(key, _):
        Handles key release events.
    update(delta_time):
        Called to update the view's state.
    """

    DEBUG = True
    PIXELS_PER_METER = .3
    #TODO: move the multiplier somewhere else
    SIM_TIMEDELTA_CONSTANT = .5
    SIM_TIME_MULTIPLIER = 1

    def __init__(self, controller, screen_width=800, screen_height=600):
        """
        Initializes the BattleshipView with a model, controller, and window properties.

        Parameters:
        -----------
        controller : BattleshipController
            The controller to handle user interactions and update the model.
        screen_width : int, optional
            The width of the screen (default is 800).
        screen_height : int, optional
            The height of the screen (default is 600).
        """
        super().__init__()
        arcade.Window.background_color = arcade.color.DARK_SKY_BLUE
        self.controller = controller
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.mouse_x = 0
        self.mouse_y = 0
        self.elapsed_time = 0
        self.simulation_time = 0
        self.pause_simulation = False
        self.restart_flag = False
        self.setup()
    
    def setup(self):
        self.status_bar = Status_Pane(self.screen_width - 150, self.screen_height / 2, 300, self.screen_height, self)
        self.playback_ui = Playback_Pane((self.screen_width - self.status_bar.width) / 2, 40, (self.screen_width - self.status_bar.width) - 100, 30, self)
        self.keys_down = {}
        
        self.ship_models = {}
        for ship_id, ship_model in self.controller.get_attribute("Simulation:World:models").items():
            self.setup_battleship(ship_id, ship_model)
        
        # Clear the ShapeList to update it
        self.obstacle_list = arcade.ShapeElementList()
        obstacle_color = arcade.color.DARK_BROWN
        for obstacle in self.controller.get_attribute("Simulation:World:obstacles"):
            if obstacle[0][0] == 1026:
                print("here")
            obstacle_shape = arcade.create_polygon(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(
                obstacle, self.PIXELS_PER_METER),
            obstacle_color)
            self.obstacle_list.append(obstacle_shape)
    
    def setup_battleship(self, model_id, model):
        if model_id in self.ship_models:
            raise KeyError(f"The View already has a model with an ID of '{model_id}'")
        self.ship_models[model_id] = {}
        current_ship = self.ship_models[model_id]

        current_ship["model"] = model
        current_ship["collision_index"] = 0
        safety_colors = [arcade.color.DARK_SPRING_GREEN, arcade.color.DEEP_CARROT_ORANGE, arcade.color.RED]
        # Create three versions of the graphic: normal, collision warning, and collision event
        current_ship["ship_shape_list"] = []
        # Calculate the dimensions and location of the ship
        battleship_coordinates = SimulatorViewUtilities.convert_coords_list_meters_to_pixels(
            self.get_model_attribute(model_id, "geometry"), self.PIXELS_PER_METER)

        # Calculate the dimensions and location of the safety ring
        battleship_ring_coordinates = SimulatorViewUtilities.convert_coords_list_meters_to_pixels(
            self.get_model_attribute(model_id, "RadarSonar:minimum_safe_area_geometry"), self.PIXELS_PER_METER)

        for i in range(3):
            # Clear the ShapeList to update it
            current_ship["ship_shape_list"].append(arcade.ShapeElementList())
            # Draw the battleship representation (a polygon)
            battleship_color = arcade.color.DIM_GRAY if i != 2 else arcade.color.BLACK
            battleship_shape = arcade.create_polygon(battleship_coordinates, battleship_color)
            current_ship["ship_shape_list"][i].append(battleship_shape)
            # Draw the battleship's safety ring representation
            battleship_safety_shape = arcade.create_line_loop(battleship_ring_coordinates, safety_colors[i], 2)
            current_ship["ship_shape_list"][i].append(battleship_safety_shape)
        current_ship["current_battleship_graphic"] = current_ship["ship_shape_list"][current_ship["collision_index"]]
    
    def on_update(self, timedelta):
        # Check the size of the window (for Linux and Mac)
        left, screen_width, bottom, screen_height = arcade.get_viewport()
        if self.screen_width != screen_width or self.screen_height != screen_height:
            self.on_resize(screen_width, screen_height)
        keys_to_remove = []
        for key_name in self.keys_down:
            if self.keys_down[key_name]["delete"]:
                keys_to_remove.append(key_name)
                continue
            self.keys_down[key_name]["timedelta"] += timedelta
            # If the timedelta exceeds the threshhold, do the action if it exists
            if not self.keys_down[key_name]["initial_wait"] and self.keys_down[key_name]["timedelta"] >= .5:
                self.keys_down[key_name]["timedelta"] -= .5
                self.keys_down[key_name]["initial_wait"] = True
                if self.keys_down[key_name]["action"] is not None:
                    self.keys_down[key_name]["action"](*self.keys_down[key_name]["args"], **self.keys_down[key_name]["kwargs"])
            elif self.keys_down[key_name]["initial_wait"] and self.keys_down[key_name]["timedelta"] >= .05:
                self.keys_down[key_name]["timedelta"] -= .05
                if self.keys_down[key_name]["action"] is not None:
                    self.keys_down[key_name]["action"](*self.keys_down[key_name]["args"], **self.keys_down[key_name]["kwargs"])
        # Remove unused keys
        if len(keys_to_remove) > 0:
            for key_to_remove in keys_to_remove:
                del self.keys_down[key_to_remove]

        if self.restart_flag:
            self.restart_simulation()
        else:
            # Force the simulation to pause if the simulation is no longer running (ended)
            if not self.controller.get_attribute("Simulation:simulation_running") and not self.pause_simulation:
                self.pause_simulation = True
                self.playback_ui.reset()
            self.elapsed_time += timedelta
            if not self.pause_simulation:
                # Update the models
                if self.controller.get_attribute("Simulation:simulation_running"):
                    # If the constant
                    sim_timedelta = self.SIM_TIMEDELTA_CONSTANT if self.SIM_TIMEDELTA_CONSTANT > 0 else timedelta
                    for _ in range(self.SIM_TIME_MULTIPLIER):
                        self.simulation_time += sim_timedelta
                        self.controller.update(sim_timedelta)
                    # The model that is displayed depends on the collision state (none, warning, event)
                    for ship_id, current_ship in self.ship_models.items():
                        if not self.get_model_attribute(ship_id, "RadarSonar:collision_warning"):
                            current_ship["collision_index"] = 0
                        elif not self.get_model_attribute(ship_id, "RadarSonar:collision_event"):
                            current_ship["collision_index"] = 1
                        else:
                            current_ship["collision_index"] = 2
                
                        # Use the correct graphic to identify the collision state
                        current_ship["current_battleship_graphic"] = current_ship["ship_shape_list"][current_ship["collision_index"]]        
                        current_ship["current_battleship_graphic"].center_x = self.get_model_attribute(ship_id, "x") * self.PIXELS_PER_METER
                        current_ship["current_battleship_graphic"].center_y = self.get_model_attribute(ship_id, "y") * self.PIXELS_PER_METER
                        current_ship["current_battleship_graphic"].angle = self.get_model_attribute(ship_id, "heading")
            else:
                playback_data = self.playback_ui.playback_data()
                # The model that is displayed depends on the collision state (none, warning, event)
                for ship_id, current_ship in self.ship_models.items():
                    if not playback_data[f"World.{ship_id}.RadarSonar.collision_warning"]:
                        current_ship["current_battleship_graphic"] = current_ship["ship_shape_list"][0]
                    elif not playback_data[f"World.{ship_id}.RadarSonar.collision_event"]:
                        current_ship["current_battleship_graphic"] = current_ship["ship_shape_list"][1]
                    else:
                        current_ship["current_battleship_graphic"] = current_ship["ship_shape_list"][2]
                    current_ship["current_battleship_graphic"].center_x = playback_data[f"World.{ship_id}.x"] * self.PIXELS_PER_METER
                    current_ship["current_battleship_graphic"].center_y = playback_data[f"World.{ship_id}.y"] * self.PIXELS_PER_METER
                    #current_ship["current_battleship_graphic"].angle = SimulatorUtilities.heading_to_angle(playback_data[f"World.{ship_id}.heading"])
                    current_ship["current_battleship_graphic"].angle = playback_data[f"World.{ship_id}.heading"]
                
            self.status_bar.update(timedelta)
            self.playback_ui.update(timedelta)
    
    def on_resize(self, width, height):
        self.status_bar.change_size(width - 150, height / 2, 300, height)
        self.playback_ui.change_size((self.screen_width - self.status_bar.width) / 2, 40, (self.screen_width - self.status_bar.width) - 100, 30)
        self.screen_width = width
        self.screen_height = height

    def on_draw(self):
        """
        Draws the battleship's representation and information on the screen.
        """

        self.clear()
        arcade.start_render()

        # If the simulation is paused, we need to pull the data from the past
        playback_data = self.playback_ui.playback_data() if self.pause_simulation else None
        
        # Draw the world
        # TODO: There is an issue rendering some polygons using the ShapeList
        #self.obstacle_list.draw()
        for obstacle in self.controller.get_attribute("Simulation:World:obstacles"):
            arcade.draw_polygon_filled(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(
                obstacle, self.PIXELS_PER_METER),
            arcade.color.DARK_BROWN)
        
        for ship_id, current_ship in self.ship_models.items():
            radar_objects = self.get_model_attribute(ship_id, 'RadarSonar:radar_objects') if playback_data is None else playback_data[f"World.{ship_id}.RadarSonar.radar_objects"]
            if len(radar_objects) > 0:
                for radar_object in radar_objects:
                    arcade.draw_polygon_filled(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(radar_object, self.PIXELS_PER_METER),
                        arcade.color.DARK_PASTEL_GREEN)
        for ship_id, current_ship in self.ship_models.items():
            warning_objects = self.get_model_attribute(ship_id, 'RadarSonar:warning_objects') if playback_data is None else playback_data[f"World.{ship_id}.RadarSonar.warning_objects"]
            if len(warning_objects) > 0:
                for warning_object in warning_objects:
                    arcade.draw_polygon_filled(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(warning_object, self.PIXELS_PER_METER),
                        arcade.color.ORANGE)
        for ship_id, current_ship in self.ship_models.items():
            collision_objects = self.get_model_attribute(ship_id, 'RadarSonar:collision_objects') if playback_data is None else playback_data[f"World.{ship_id}.RadarSonar.collision_objects"]
            if len(collision_objects) > 0:
                for collision_object in collision_objects:
                    arcade.draw_polygon_filled(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(collision_object, self.PIXELS_PER_METER),
                        arcade.color.RED)
            # Draw the radar range
            radar_geometry = self.get_model_attribute(ship_id, 'RadarSonar:radar_geometry') if playback_data is None else playback_data[f"World.{ship_id}.RadarSonar.radar_geometry"]
            arcade.draw_polygon_outline(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(radar_geometry, self.PIXELS_PER_METER), arcade.color.DIM_GRAY, 2)

        # Draw each ship in the simulation
        for ship_id, current_ship in self.ship_models.items():
            # Draw the waypoints
            completed_waypoints = self.get_model_attribute(ship_id, "Navigation:completed_waypoints") if playback_data is None else playback_data[f"World.{ship_id}.Navigation.completed_waypoints"]
            waypoints = self.get_model_attribute(ship_id, "Navigation:waypoints") if playback_data is None else playback_data[f"World.{ship_id}.Navigation.waypoints"]
            all_waypoints = completed_waypoints + waypoints
            if len(all_waypoints) > 0:
                for i, waypoint in enumerate(all_waypoints):
                    foreground_color = arcade.color.BLACK if waypoint in waypoints else arcade.color.DARK_GRAY
                    background_color = arcade.color.YELLOW if waypoint in waypoints else arcade.color.GRAY
                    waypoint = SimulatorViewUtilities.convert_coords_meters_to_pixels(*waypoint, self.PIXELS_PER_METER)
                    arcade.draw_circle_filled(waypoint[0], waypoint[1], self.get_model_attribute(ship_id, "Navigation:ALLOWED_DISTANCE_ERROR") * self.PIXELS_PER_METER, background_color + (192,))
                    arcade.draw_point(waypoint[0], waypoint[1], foreground_color, 4)
                    arcade.draw_text(f"{ship_id} - Waypoint {i + 1}", waypoint[0] + 4, waypoint[1] + 4, foreground_color, font_size = 14)
            
            # Draw targets
            targets = self.get_model_attribute(ship_id, "Weapons:targets") if playback_data is None else playback_data[f"World.{ship_id}.Weapons.targets"]
            if len(targets) > 0:
                for i, target in enumerate(targets):
                    foreground_color = arcade.color.BLACK if target in targets else arcade.color.DARK_GRAY
                    background_color = arcade.color.RED if target in targets else arcade.color.GRAY
                    target = SimulatorViewUtilities.convert_coords_meters_to_pixels(*target, self.PIXELS_PER_METER)
                    arcade.draw_circle_filled(target[0], target[1], 20 * self.PIXELS_PER_METER, background_color + (192,))
                    arcade.draw_circle_outline(target[0], target[1], 40 * self.PIXELS_PER_METER, background_color + (192,), 10 * self.PIXELS_PER_METER)
                    arcade.draw_circle_outline(target[0], target[1], 60 * self.PIXELS_PER_METER, background_color + (192,), 10 * self.PIXELS_PER_METER)
                    arcade.draw_point(target[0], target[1], foreground_color, 4)
                    arcade.draw_text(f"{ship_id} - Target {i + 1}", target[0] + 4, target[1] + 4, foreground_color, font_size = 14)
            # Draw the path taken
            if not self.pause_simulation or self.playback_ui.current_index == self.playback_ui.max_index:
                current_path = self.get_model_attribute(ship_id, "Navigation:actual_path")
                future_path = []
            else:
                complete_path = self.get_model_attribute(ship_id, "Navigation:actual_path")
                current_path = complete_path[:self.playback_ui.current_index + 1]
                future_path = complete_path[self.playback_ui.current_index + 1:]
            arcade.draw_line_strip(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(
                current_path, self.PIXELS_PER_METER),
                arcade.color.DARK_BLUE)
            if len(future_path) > 0:
                arcade.draw_line_strip(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(
                future_path, self.PIXELS_PER_METER),
                arcade.color.BLUE_GRAY)
            
            # Draw the ships
            current_ship["current_battleship_graphic"].draw()

            # Debugging tools
            if self.DEBUG:
                # Draw the heading information
                current_heading_line = SimulatorUtilities.calculate_line_coordinates_from_center(
                    current_ship["current_battleship_graphic"].center_x,
                    current_ship["current_battleship_graphic"].center_y,
                    300,
                    current_ship["current_battleship_graphic"].angle
                )
                current_heading_text_line = SimulatorUtilities.calculate_line_coordinates_from_center(
                    current_ship["current_battleship_graphic"].center_x,
                    current_ship["current_battleship_graphic"].center_y,
                    370,
                    current_ship["current_battleship_graphic"].angle
                )
                north_heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                    current_ship["current_battleship_graphic"].center_x,
                    current_ship["current_battleship_graphic"].center_y,
                    125,
                    90
                )
                chosen_heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                    current_ship["current_battleship_graphic"].center_x,
                    current_ship["current_battleship_graphic"].center_y,
                    150,
                    self.get_model_attribute(ship_id, "waypoint_heading") if playback_data is None else playback_data[f"World.{ship_id}.waypoint_heading"]
                )
                chosen_heading_text_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                    current_ship["current_battleship_graphic"].center_x,
                    current_ship["current_battleship_graphic"].center_y,
                    250,
                    self.get_model_attribute(ship_id, "waypoint_heading") if playback_data is None else playback_data[f"World.{ship_id}.waypoint_heading"]
                )
                port_option_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                    current_heading_line[2],
                    current_heading_line[3],
                    50,
                    current_ship["current_battleship_graphic"].angle + 90
                )
                port_option_text_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                    current_heading_line[2],
                    current_heading_line[3],
                    90,
                    current_ship["current_battleship_graphic"].angle + 90
                )
                starboard_option_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                    current_heading_line[2],
                    current_heading_line[3],
                    50,
                    current_ship["current_battleship_graphic"].angle - 90
                )
                starboard_option_text_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                    current_heading_line[2],
                    current_heading_line[3],
                    90,
                    current_ship["current_battleship_graphic"].angle - 90
                )
                
                arcade.draw_line(*current_heading_line, arcade.color.BLUE)

                chosen_direction = self.get_model_attribute(ship_id, 'chosen_direction') if playback_data is None else playback_data[f"World.{ship_id}.chosen_direction"]
                color = arcade.color.RED if chosen_direction == "port" else arcade.color.DIM_GRAY
                arcade.draw_line(*port_option_line, color)
                arcade.draw_point(port_option_line[2], port_option_line[3], color, 6)
                arcade.draw_text(f"{round(self.get_model_attribute(ship_id, 'option_port') if playback_data is None else playback_data[f'World.{ship_id}.option_port'], 2)}°", port_option_text_line[2], port_option_text_line[3], color, anchor_x="center", anchor_y="center", font_size = 14)

                color = arcade.color.ISLAMIC_GREEN if chosen_direction == "starboard" else arcade.color.DIM_GRAY
                arcade.draw_line(*starboard_option_line, color)
                arcade.draw_point(starboard_option_line[2], starboard_option_line[3], color, 6)
                arcade.draw_text(f"{round(self.get_model_attribute(ship_id, 'option_starboard') if playback_data is None else playback_data[f'World.{ship_id}.option_starboard'], 2)}°", starboard_option_text_line[2], starboard_option_text_line[3], color, anchor_x="center", anchor_y="center", font_size = 14)
                
                arcade.draw_point(current_heading_line[2], current_heading_line[3], arcade.color.BLUE, 6)
                arcade.draw_text(f"{round(self.get_model_attribute(ship_id, 'heading') if playback_data is None else playback_data[f'World.{ship_id}.heading'], 2)}°", current_heading_text_line[2], current_heading_text_line[3], arcade.color.BLUE, anchor_x="center", anchor_y="center", font_size = 14)
                arcade.draw_line(*north_heading_line, arcade.color.BLUE)
                arcade.draw_line(*chosen_heading_line, arcade.color.BLACK)
                arcade.draw_point(chosen_heading_line[2], chosen_heading_line[3], arcade.color.BLACK, 6)
                arcade.draw_text(f"{round(self.get_model_attribute(ship_id, 'waypoint_heading') if playback_data is None else playback_data[f'World.{ship_id}.waypoint_heading'], 2)}°", chosen_heading_text_line[2], chosen_heading_text_line[3], arcade.color.BLACK, anchor_x="center", anchor_y="center", font_size = 14)

                arcade.draw_text(ship_id, (self.get_model_attribute(ship_id, 'x') if playback_data is None else playback_data[f'World.{ship_id}.x']) * self.PIXELS_PER_METER, (self.get_model_attribute(ship_id, 'y') if playback_data is None else playback_data[f'World.{ship_id}.y']) * self.PIXELS_PER_METER - 50, arcade.color.BLACK, anchor_x="center", anchor_y="center", font_size = 14)

                if self.pause_simulation and self.playback_ui.current_index == self.playback_ui.max_index and self.get_model_attribute(ship_id, "user_override_heading") is not None:
                    override_heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                        current_ship["current_battleship_graphic"].center_x,
                        current_ship["current_battleship_graphic"].center_y,
                        150,
                        (self.get_model_attribute(ship_id, "user_override_heading"))
                    )
                    override_heading_text_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                        current_ship["current_battleship_graphic"].center_x,
                        current_ship["current_battleship_graphic"].center_y,
                        200,
                        (self.get_model_attribute(ship_id, "user_override_heading"))
                    )
                    arcade.draw_line(*override_heading_line, arcade.color.YELLOW)
                    arcade.draw_point(override_heading_line[2], override_heading_line[3], arcade.color.YELLOW, 6)
                    arcade.draw_text(f"{self.get_model_attribute(ship_id, 'user_override_heading')}°", override_heading_text_line[2], override_heading_text_line[3], arcade.color.YELLOW, anchor_x="center", anchor_y="center", font_size = 14)
                elif (self.get_model_attribute(ship_id, 'user_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.user_override_heading']) is not None:
                    override_heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                        current_ship["current_battleship_graphic"].center_x,
                        current_ship["current_battleship_graphic"].center_y,
                        150,
                        (self.get_model_attribute(ship_id, 'user_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.user_override_heading'])
                    )
                    override_heading_text_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                        current_ship["current_battleship_graphic"].center_x,
                        current_ship["current_battleship_graphic"].center_y,
                        200,
                        (self.get_model_attribute(ship_id, 'user_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.user_override_heading'])
                    )
                    arcade.draw_line(*override_heading_line, arcade.color.YELLOW)
                    arcade.draw_point(override_heading_line[2], override_heading_line[3], arcade.color.YELLOW, 6)
                    arcade.draw_text(f"{round(self.get_model_attribute(ship_id, 'user_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.user_override_heading'], 2)}°", override_heading_text_line[2], override_heading_text_line[3], arcade.color.YELLOW, anchor_x="center", anchor_y="center", font_size = 14)
                
                if (self.get_model_attribute(ship_id, 'ca_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.ca_override_heading']) is not None:
                    override_heading_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                        current_ship["current_battleship_graphic"].center_x,
                        current_ship["current_battleship_graphic"].center_y,
                        150,
                        self.get_model_attribute(ship_id, 'ca_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.ca_override_heading']
                    )
                    override_heading_text_line = SimulatorUtilities.calculate_line_coordinates_from_end(
                        current_ship["current_battleship_graphic"].center_x,
                        current_ship["current_battleship_graphic"].center_y,
                        200,
                        self.get_model_attribute(ship_id, 'ca_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.ca_override_heading']
                    )
                    arcade.draw_line(*override_heading_line, arcade.color.DEEP_CARROT_ORANGE)
                    arcade.draw_point(override_heading_line[2], override_heading_line[3], arcade.color.DEEP_CARROT_ORANGE, 6)
                    arcade.draw_text(f"{round(self.get_model_attribute(ship_id, 'ca_override_heading') if playback_data is None else playback_data[f'World.{ship_id}.ca_override_heading'], 2)}°", override_heading_text_line[2], override_heading_text_line[3], arcade.color.DEEP_CARROT_ORANGE, anchor_x="center", anchor_y="center", font_size = 14)

                    for coll_object in (self.get_model_attribute(ship_id, 'CollisionAvoidance:relevant_objects') if playback_data is None else playback_data[f'World.{ship_id}.CollisionAvoidance.relevant_objects']):
                         arcade.draw_polygon_outline(SimulatorViewUtilities.convert_coords_list_meters_to_pixels(coll_object, self.PIXELS_PER_METER), arcade.color.BLACK, 1)

            arcade.draw_text(f"{self.playback_ui.max_index}", self.status_bar.min_x - 5, self.screen_height, arcade.color.BLACK, anchor_x = "right", anchor_y = "top", font_size = 16)

        if self.pause_simulation:
            self.playback_ui.draw()
        self.status_bar.draw()

        if self.controller.get_attribute("Simulation:simulation_running"):
            arcade.draw_text(f"Press <SPACE> to {'pause' if not self.pause_simulation else 'resume'} or <ENTER> to restart", 5, self.screen_height, arcade.color.BLACK, anchor_x = "left", anchor_y = "top", font_size = 16)
        else:
            arcade.draw_text(f"Result: {self.controller.get_attribute('Simulation:simulation_status')}; press <ENTER> to restart", 5, self.screen_height, arcade.color.BLACK, anchor_x = "left", anchor_y = "top", font_size = 16)
        if arcade.get_window().fullscreen:
            arcade.draw_text("Press <ESC> to exit fullscreen", 5, self.screen_height - 24, arcade.color.BLACK, anchor_x = "left", anchor_y = "top", font_size = 16)

    def on_mouse_press(self, x, y, button, key_modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.pause_simulation:
                slider_left, slider_bottom, slider_width, slider_height = self.playback_ui.slider_area()
                if slider_left <= x <= slider_left + slider_width and slider_bottom <= y <= slider_bottom + slider_height:
                    self.playback_ui.slider_selected = True
                else:
                    playback_left, playback_bottom, playback_width, playback_height = self.playback_ui.playback_area()
                    if playback_left <= x <= playback_left + playback_width and playback_bottom <= y <= playback_bottom + playback_height:
                        self.playback_ui.update_slider_x(x)
                        self.playback_ui.slider_selected = True
                    else:
                        for button in ["back", "next"]:
                            button_left, button_bottom, button_width, button_height = self.playback_ui.button_area(button)
                            if button_left <= x <= button_left + button_width and button_bottom <= y <= button_bottom + button_height:
                                self.playback_ui.increment_index(1 if button == "next" else -1)
            
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        if self.playback_ui.slider_selected:
            self.playback_ui.update_slider_x(x)
    
    def on_mouse_release(self, x, y, button, key_modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.pause_simulation:
                self.playback_ui.slider_selected = False

    def on_key_press(self, key, _):
        """
        Handles key press events, triggering appropriate actions.

        Parameters:
        -----------
        key : int
            The key code of the pressed key.
        _ : int
            Modifiers for the key press, not used here.
        """
        if key in self.keys_down:
            return
        
        self.keys_down[key] = {
            "timedelta": 0,
            "initial_wait": False,
            "action": None,
            "args": [],
            "kwargs": {},
            "delete": False
        }
        match(key):
            case arcade.key.ESCAPE:
                if arcade.get_window().fullscreen:
                    arcade.get_window().set_fullscreen(False)
                    # Get the window coordinates. Match viewport to window coordinates
                    # so there is a one-to-one mapping.
                    width, height = arcade.get_window().get_size()
                    arcade.get_window().set_viewport(0, width, 0, height)
            case arcade.key.SPACE:
                # We don't want this to repeat, so we don't add it as an action
                self.spacebar_action()
            case arcade.key.ENTER:
                self.restart_flag = True
            case arcade.key.LEFT:
                self.keys_down[key]["action"] = self.left_action
                self.left_action()
            case arcade.key.RIGHT:
                self.keys_down[key]["action"] = self.right_action
                self.right_action()
            case arcade.key.BACKSPACE:
                self.backspace_action()
    
    def spacebar_action(self):
        # If the simulation is not running, then disable this command (forced pause)
        if self.controller.get_attribute("Simulation:simulation_running"):
            self.pause_simulation = not self.pause_simulation
            if self.pause_simulation:
                self.controller.get_child("Simulation").pause()
                self.playback_ui.reset()
            else:
                self.controller.get_child("Simulation").resume()
    
    def left_action(self):
        # Turn to port (positive using mathematical angle)
        if self.controller.get_attribute("Simulation:simulation_running"):
            self.pause_simulation = True
            self.controller.get_child("Simulation").pause()
            self.playback_ui.reset()
            
            if self.get_model_attribute("PrimaryBattleship", "user_override_heading") is None:
                self.set_model_attribute("PrimaryBattleship", "user_override_heading", self.get_model_attribute("PrimaryBattleship", "heading"))
                if self.get_model_attribute("PrimaryBattleship", "user_override_heading") < 0:
                    self.set_model_attribute("PrimaryBattleship", "user_override_heading", self.get_model_attribute("PrimaryBattleship", "user_override_heading") + 360)
            
            self.set_model_attribute("PrimaryBattleship", "user_override_heading", round(self.get_model_attribute("PrimaryBattleship", "user_override_heading") + 1))
            if self.get_model_attribute("PrimaryBattleship", "user_override_heading") >= 360:
                self.set_model_attribute("PrimaryBattleship", "user_override_heading", 0)
    
    def right_action(self):
        # Turn to starboard (negative using mathematical angle)
        if self.controller.get_attribute("Simulation:simulation_running"):
            self.pause_simulation = True
            self.controller.get_child("Simulation").pause()
            self.playback_ui.reset()

            if self.get_model_attribute("PrimaryBattleship", "user_override_heading") is None:
                self.set_model_attribute("PrimaryBattleship", "user_override_heading", self.get_model_attribute("PrimaryBattleship", "heading"))
                if self.get_model_attribute("PrimaryBattleship", "user_override_heading") > 0:
                    self.set_model_attribute("PrimaryBattleship", "user_override_heading", self.get_model_attribute("PrimaryBattleship", "user_override_heading") - 360)
            
            self.set_model_attribute("PrimaryBattleship", "user_override_heading", round(self.get_model_attribute("PrimaryBattleship", "user_override_heading") - 1))
            if self.get_model_attribute("PrimaryBattleship", "user_override_heading") <= -360:
                self.set_model_attribute("PrimaryBattleship", "user_override_heading", 0)
    
    def backspace_action(self):
        if self.controller.get_attribute("Simulation:simulation_running"):
            self.pause_simulation = True
            self.controller.get_child("Simulation").pause()
            self.playback_ui.reset()

            self.set_model_attribute("PrimaryBattleship", "user_override_heading", None)

    def on_key_release(self, key, _):
        """
        Handles key release events.

        Parameters:
        -----------
        key : int
            The key code of the released key.
        _ : int
            Modifiers for the key release, not used here.
        """
        # Wait for the update() to delete the key entry so we don't have a race condition
        self.keys_down[key]["delete"] = True

    def restart_simulation(self):
        self.controller.restart()
        self.restart_flag = False
        self.pause_simulation = False

    def get_model_attribute(self, model_id, attribute):
        return self.controller.get_attribute(f"Simulation:World:{model_id}:{attribute}")

    def set_model_attribute(self, model_id, attribute, value):
        self.controller.set_attribute(f"Simulation:World:{model_id}:{attribute}", value)

class Status_Pane():

    STD_OFFSET = 5

    def __init__(self, x, y, width, height, parent_view, tracked_object = "PrimaryBattleship"):

        self.text_objects = [None, None, None]
        self.change_size(x, y, width, height)
        self.parent_view = parent_view
        self.tracked_object = tracked_object
        self.setup()

    def setup(self):
        self.update(0)

    def update(self, timedelta):
        # Index 0 is keys
        # Index 1 is values
        # Index 2 is headings
        text_strings = ["","",""]
        self.monitored_data = {
            "----- Model Data -----": {
                "Ship X": round(self.parent_view.get_model_attribute(self.tracked_object, 'x')),
                "Ship Y": round(self.parent_view.get_model_attribute(self.tracked_object, 'y')),
                "Speed": f"{round(self.parent_view.get_model_attribute(self.tracked_object, 'current_speed'), 1)} m/s",
                "Heading": f"{round(self.parent_view.get_model_attribute(self.tracked_object, 'heading'))}°",
                "Chosen Heading": f"{round(self.parent_view.get_model_attribute(self.tracked_object, 'chosen_heading'))}°",
                "Action": self.parent_view.get_model_attribute(self.tracked_object, 'actions'),
                "Col. Warning": self.parent_view.get_model_attribute(self.tracked_object, "RadarSonar:collision_warning"),
                "Col. Event": self.parent_view.get_model_attribute(self.tracked_object, "RadarSonar:collision_event")
            },
            "----- View Data -----": {
                "Sim Time": SimulatorViewUtilities.seconds_to_hms(self.parent_view.simulation_time),
                "Sim Time Delta": f"{round(self.parent_view.controller.get_attribute('Simulation:timedelta'), 2)} s",
                "Frame Rate": f"{int(arcade.get_fps())} FPS",
                "Mouse X (px)": self.parent_view.mouse_x,
                "Mouse Y (px)": self.parent_view.mouse_y,
                "Mouse X (m)": round(self.parent_view.mouse_x / self.parent_view.PIXELS_PER_METER, 2),
                "Mouse Y (m)": round(self.parent_view.mouse_y / self.parent_view.PIXELS_PER_METER, 2),
            },
            #"----- Log Data -----": {k.rsplit(".")[-1]:v for k, v in self.parent_view.controller.world.logging_package().items()}
        }
        for section in self.monitored_data:
            text_strings[0] += "\n"
            text_strings[1] += "\n"
            text_strings[2] += section + "\n"
            for key, value in self.monitored_data[section].items():
                text_strings[2] += "\n"
                text_strings[0] += key + "\n"
                text_strings[1] += str(value) + "\n"
            text_strings[0] += "\n"
            text_strings[1] += "\n"
            text_strings[2] += "\n"

        if self.text_objects[0] is None:
            self.text_objects[0] = arcade.Text("", 0, 0, arcade.color.WHITE, 12, self.width / 2, anchor_x="left", anchor_y = "top", multiline=True)
            self.text_objects[1] = arcade.Text("", 0, 0, arcade.color.WHITE, 12, self.width / 2, anchor_x="left", anchor_y = "top", multiline=True)
            self.text_objects[2] = arcade.Text("", 0, 0, arcade.color.YELLOW, 12, self.width, anchor_x = "center", anchor_y = "top", align = "center", multiline=True)
        
        # Update the object's properties to minimize the number of times it is redrawn (halves the frame rate to just rebuild the object for some reason)
        for i in range(len(self.text_objects)):
            if self.text_objects[i].text != text_strings[i]:
                self.text_objects[i].text = text_strings[i]
            # The x-position for the headings is different from the rest
            if i == 0:
                if self.text_objects[i].x != self.min_x + 10:
                    self.text_objects[i].x = self.min_x + 10
            else:
                if self.text_objects[i].x != self.min_x + (self.width / 2):
                    self.text_objects[i].x = self.min_x + (self.width / 2)
            # All the y-positions are the same
            if self.text_objects[i].y != self.max_y - 10:
                self.text_objects[i].y = self.max_y - 10
    
    def draw(self):
        arcade.draw_rectangle_filled(self.x, self.y, self.width, self.height, arcade.color.BLACK)
        for text_object in self.text_objects:
            text_object.draw()
    
    def change_size(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_x = x + width // 2
        self.min_x = self.max_x - width
        self.max_y = y + height // 2
        self.min_y = self.max_y - height

class Playback_Pane():

    def __init__(self, x, y, width, height, parent_view):
        self.buttons = {}
        for button in ["back", "next"]:
            self.buttons[button] = {
                "min_x": 0,
                "x": 0,
                "max_x": 0
            }
        self.change_size(x, y, width, height)
        self.parent_view = parent_view
        self.current_index = 0
        self.max_index = 0
        self.slider_selected = False
        self.slider_x = self.max_x

    def update(self, timedelta):
        self.max_index = self.parent_view.controller.get_attribute("Simulation:Logger:length") - 1

    def draw(self):
        arcade.draw_rectangle_filled(self.bar_x, self.y, self.bar_width, self.height, arcade.color.RED)
        if self.slider_x < self.bar_max_x:
            arcade.draw_rectangle_filled(self.slider_x + ((self.bar_max_x - self.slider_x) / 2), self.y, self.bar_max_x - self.slider_x, self.height, arcade.color.LIGHT_GRAY)
        arcade.draw_rectangle_outline(self.bar_x, self.y, self.bar_width, self.height, arcade.color.BLACK)
        if self.max_index > 0:
            arcade.draw_rectangle_filled(self.slider_x, self.y, 10, self.height + 10, arcade.color.DARK_RED)
            arcade.draw_rectangle_outline(self.slider_x, self.y, 10, self.height + 10, arcade.color.BLACK)
        arcade.draw_text(self.current_index, self.x, self.y, arcade.color.BLACK, anchor_x = "center", anchor_y = "center")

        for button in self.buttons.values():
            arcade.draw_rectangle_filled(button["x"], self.y, self.button_width, self.height, arcade.color.WHITE)
            arcade.draw_rectangle_outline(button["x"], self.y, self.button_width, self.height, arcade.color.BLACK)
            arcade.draw_text("<<" if button is self.buttons["back"] else ">>", button["x"], self.y, arcade.color.BLACK, anchor_x="center", anchor_y="center")
    
    def reset(self):
        self.current_index = self.max_index
        self.slider_x = self.bar_max_x
        self.slider_selected = False
    
    def playback_data(self):
        return self.parent_view.controller.logger_get(self.current_index)
    
    def button_area(self, button_id):
        # left, bottom, width, height
        return (
            int(self.buttons[button_id]["min_x"]),
            int(self.min_y),
            self.button_width,
            self.button_width
        )
    
    def slider_area(self):
        # left, bottom, width, height
        return (
            int(self.slider_x - (self.slider_width / 2)),
            int(self.y - (self.slider_height / 2)),
            self.slider_width,
            self.slider_height
        )
    
    def playback_area(self):
        # left, bottom, width, height
        return (
            self.min_x,
            self.min_y,
            self.bar_width,
            self.height
        )

    def update_slider_x(self, new_x):
        if self.min_x <= new_x <= self.bar_max_x:
            self.slider_x = new_x
        elif self.min_x > new_x:
            self.slider_x = self.min_x
        else:
            self.slider_x = self.bar_max_x
        # Get the index
        slider_pct = (self.slider_x - self.min_x) / self.bar_width
        self.current_index = round(self.max_index * slider_pct)
        # Snap the slider to the index's position on the bar
        self.slider_x = round(self.min_x + (self.bar_width * (self.current_index / self.max_index)))
    
    def increment_index(self, i):
        if 0 <= self.current_index + i <= self.max_index:
            self.current_index = self.current_index + i
            # Snap the slider to the index's position on the bar
            self.slider_x = round(self.min_x + (self.bar_width * (self.current_index / self.max_index)))

    def change_size(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_x = x + width // 2
        self.min_x = self.max_x - width
        self.max_y = y + height // 2
        self.min_y = self.max_y - height
                
        self.button_width = self.height
        padding = 5
        bar_width = self.width - (len(self.buttons) * (self.button_width + padding)) + padding
        self.bar_x = self.min_x + (bar_width / 2)
        self.bar_max_x = self.min_x + bar_width
        self.bar_width = self.bar_max_x - self.min_x

        self.slider_x = self.bar_max_x
        self.slider_width = 16
        self.slider_height = self.height + 10

        for i, button in enumerate(self.buttons.values()):
            button["min_x"] = self.bar_max_x + (padding * 2) + ((padding + self.button_width) * i)
            button["x"] = button["min_x"] + (self.button_width / 2)
            button["max_x"] = button["min_x"] + self.button_width