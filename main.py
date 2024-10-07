# Import modules from the Battleship package instead of individual classes
import BattleshipSimulator.BattleshipController as BattleCtrl
import BattleshipSimulator.Models.Environment as Environment
import BattleshipSimulator.Views.BattleshipView as BattleGUI
import arcade
import argparse
import os
import glob

# Constants for the screen width and height
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768

def parse_arguments():
    """ Parse the arguments provided with the start command

    Returns
    -------
    argparse.Namespace
        The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Process mode and scenario")
    # Adding the 'mode' argument with a default value
    parser.add_argument('--mode', type=str, default='gui',
                        help='Mode of operation. Default is "gui".')
    # Adding the 'scenario' argument with a default value
    parser.add_argument('--scenario', type=str, default="scenarios/scenario-gen-0.yaml",
                        help='Scenario to run. Default is "scenarios/scenario-gen-0.yaml".')
    # Parse the arguments
    args = parser.parse_args()
    return args

def get_yaml_files(directory):
    """ List the YAML files in a directory

    This function examines all files in the provided directory and lists YAML files

    Parameters
    ----------
    directory : str
        The directory to search in

    Returns
    -------
    list
        The paths to files that end in .yaml or .yml
    """
    # Check if the specified directory exists
    if not os.path.isdir(directory):
        raise ValueError(f"The directory {directory} does not exist.")
    # Use glob to find .yaml and .yml files
    yaml_files = glob.glob(os.path.join(directory, '*.yaml'))
    yml_files = glob.glob(os.path.join(directory, '*.yml'))
    # Combine the lists
    all_yaml_files = yaml_files + yml_files
    return all_yaml_files

def main():
    """ The entry point into the application
    """
    args = parse_arguments()
    # If the scenario is a directory, run all the scenarios contained within it
    # This mode forces the program to operate in CLI
    if os.path.isdir(args.scenario):
        for scenario_cfg in get_yaml_files(args.scenario):
            simulator = Environment.Simulator(scenario_cfg)
            controller = BattleCtrl.BattleshipController(simulator)
            simulator.start()
            view = BattleGUI.BattleshipViewCLI(controller)
            view.start()
    # Else, run a single scenario
    else:
        simulator = Environment.Simulator(args.scenario)
        controller = BattleCtrl.BattleshipController(simulator)
        simulator.start()
        # If the mode is "gui", run the application with the GUI
        if args.mode == "gui":
            # Create the controller and view, set up the window, and start the GUI loop
            window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Battleship Simulator", fullscreen = True)
            view = BattleGUI.BattleshipViewGUI(controller, SCREEN_WIDTH, SCREEN_HEIGHT)
            window.show_view(view)
            arcade.enable_timings()
            arcade.run()
        # Else, run the application with the CLI
        else:
            view = BattleGUI.BattleshipViewCLI(controller)
            view.start()

if __name__ == "__main__":
    main()
