from opcua import Server
import zmq
import json
import time
import random
from icecream import ic

ic.configureOutput(includeContext=True, contextAbsPath=True)

def calculate_power(speed_m_per_s, rho=1025, cd=0.035, area_m2=1005):
    drag_force = 0.5 * cd * rho * area_m2 * speed_m_per_s ** 2
    power = drag_force * speed_m_per_s

    return power

def main():
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840")
    add_space = server.register_namespace("OPCUA_BATTLESHIP_DATA_SERVER")

    node = server.get_objects_node()
    param = node.add_object(add_space, "Parameters")

    keys_to_extract = [
        "simulation_status",
        "World.PrimaryBattleship.x",
        "World.PrimaryBattleship.y",
        "World.PrimaryBattleship.heading",
        "World.PrimaryBattleship.waypoint_heading",
        "World.PrimaryBattleship.supervisor_override",
        "World.PrimaryBattleship.current_speed",        
        "World.PrimaryBattleship.Engine.desired_speed"
    ]

    opcua_variables = {}
    for i, key in enumerate(keys_to_extract, start=2):
        default_value = 0 if "speed" in key or "heading" in key else "None"
        opcua_variables[key] = param.add_variable(add_space, f"ns=2;i={i}", default_value)
        opcua_variables[key].set_writable()

    power = param.add_variable(add_space, "ns=2;i=10", 0)
    power.set_writable()

    server.start()
    print("Server started at opc.tcp://0.0.0.0:4840")

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://battleship:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')

    

    while True:
            
        message = socket.recv_string()
        try:
            data = json.loads(message)
            for key in keys_to_extract:
                value = data.get(key)
                if value is not None:
                    opcua_variables[key].set_value(value)
                    if key == "World.PrimaryBattleship.Engine.desired_speed":
                        power_watts = calculate_power(value)

                        # Fluctuate power by ±7% at each update
                        fluctuation_factor = random.uniform(0.93, 1.08)
                        fluctuated_power_watts = power_watts * fluctuation_factor
                        power_megawatts = fluctuated_power_watts / 1e6
                        power.set_value(power_megawatts)
                        print(f"This is the current power: {power_megawatts}")

        except json.JSONDecodeError as e:
            print(f"Invalid JSON received: {message} Error: {str(e)}")
        time.sleep(0.001)

if __name__ == "__main__":
    main()
