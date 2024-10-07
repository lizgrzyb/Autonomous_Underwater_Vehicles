## Directory Hierarchy
```
|—— BattleshipController.py
|—— Models
|    |—— BattleshipModel.py
|    |—— BattleshipSystem.py
|    |—— Environment.py
|    |—— GetterSetter.py
|    |—— Logger.py
|    |—— SimulatorUtilities.py
|    |—— SimulatorViewUtilities.py
|    |—— __init__.py
|    |—— __pycache__
|        |—— BattleshipModel.cpython-310.pyc
|        |—— BattleshipSystem.cpython-310.pyc
|        |—— Environment.cpython-310.pyc
|        |—— GetterSetter.cpython-310.pyc
|        |—— Logger.cpython-310.pyc
|        |—— SimulatorUtilities.cpython-310.pyc
|        |—— SimulatorViewUtilities.cpython-310.pyc
|        |—— __init__.cpython-310.pyc
|—— Supervisor
|    |—— Navigators.py
|    |—— __init__.py
|    |—— __pycache__
|        |—— Navigators.cpython-310.pyc
|        |—— __init__.cpython-310.pyc
|—— Views
|    |—— BattleshipView.py
|    |—— __pycache__
|        |—— BattleshipView.cpython-310.pyc
|—— __init__.py
|—— __pycache__
|    |—— BattleshipController.cpython-310.pyc
|    |—— __init__.cpython-310.pyc
|—— python_vehicle_simulator
|    |—— 3D_animation.gif
|    |—— lib
|        |—— __init__.py
|        |—— __pycache__
|            |—— __init__.cpython-310.pyc
|            |—— control.cpython-310.pyc
|            |—— gnc.cpython-310.pyc
|            |—— guidance.cpython-310.pyc
|            |—— mainLoop.cpython-310.pyc
|            |—— models.cpython-310.pyc
|            |—— plotTimeSeries.cpython-310.pyc
|        |—— control.py
|        |—— gnc.py
|        |—— guidance.py
|        |—— mainLoop.py
|        |—— models.py
|        |—— plotTimeSeries.py
|    |—— vehicles
|        |—— DSRV.py
|        |—— ROVzefakkel.py
|        |—— __init__.py
|        |—— __pycache__
|            |—— DSRV.cpython-310.pyc
|            |—— ROVzefakkel.cpython-310.pyc
|            |—— __init__.cpython-310.pyc
|            |—— frigate.cpython-310.pyc
|            |—— otter.cpython-310.pyc
|            |—— remus100.cpython-310.pyc
|            |—— semisub.cpython-310.pyc
|            |—— shipClarke83.cpython-310.pyc
|            |—— supply.cpython-310.pyc
|            |—— tanker.cpython-310.pyc
|        |—— frigate.py
|        |—— otter.py
|        |—— remus100.py
|        |—— semisub.py
|        |—— shipClarke83.py
|        |—— supply.py
|        |—— tanker.py
|—— resources
|    |—— test_sprite.png
```
## Code Details

Models - Contains code for modeling and simulating the battleship and a native GUI (important files: BattleshipModel.py and SimulatorUtilities.py)
python_vehicle_simulator - Library code imported from [PythonVehicleSimulator](https://github.com/cybergalactic/PythonVehicleSimulator)
resources - Static assets used in GUI
Supervisor - Contains supervisor classes for managing decisions of the battleship (collision avoidance is in CollisionAvoidanceNavigator in Navigators.py)
Views - Code for the GUI of the battleship

