from BattleshipSimulator.Models.GetterSetter import GetterSetter

class BattleshipController(GetterSetter):
    """
    The controller in the MVC architecture. Handles user interactions and updates the model.

    Attributes:
    -----------
    model : BattleshipModel
        The model representing the battleship's data and state.
    """
    
    def __init__(self, simulation):
        """
        Initializes the BattleshipController with a model.

        Parameters:
        -----------
        model : BattleshipModel
            The model representing the battleship's data and state.
        """
        super().__init__()
        self.simulation = simulation
        self.add_child("Simulation", self.simulation)
    
    def restart(self):
        self.simulation.restart()
        self.__init__(self.simulation)
        self.simulation.start()
    
    def update(self, timedelta):
        if self.simulation.simulation_running:
            self.simulation.update(timedelta)

    def logger_get(self, index):
        return self.simulation.logger.get(index)

    def handle_action(self, action):
        """
        Handle user actions and update the model.

        Parameters:
        -----------
        action : str
            The user action to handle.
        """
        self.model.handle_command(action)