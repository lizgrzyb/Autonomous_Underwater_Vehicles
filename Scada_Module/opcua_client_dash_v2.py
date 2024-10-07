from opcua import Client
import paho.mqtt.client as mqtt
import time
import json
import random
from icecream import ic

ic.configureOutput(includeContext=True, contextAbsPath=True)

def apply_power_fluctuation(power_value):
    fluctuation_factor = random.uniform(0.93, 1.08)  # ±7% fluctuation
    return power_value * fluctuation_factor

def main():
    client = Client("opc.tcp://opcua_server:4840")
    client.connect()
    print("OPC UA Client connected")

    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set("EfNBzauFCrlWTctinSyT", "")
    mqtt_client.connect("kr4k3n.thingsboard.io", 1883)
    print("Connected to ThingsBoard")

    key_mappings = {
        "ns=2;i=2": "simulation_status",
        "ns=2;i=3": "World.PrimaryBattleship.x",
        "ns=2;i=4": "World.PrimaryBattleship.y",
        "ns=2;i=5": "World.PrimaryBattleship.heading",
        "ns=2;i=6": "World.PrimaryBattleship.waypoint_heading",
        "ns=2;i=7": "World.PrimaryBattleship.supervisor_override",
        "ns=2;i=8": "World.PrimaryBattleship.current_speed",
        "ns=2;i=9": "World.PrimaryBattleship.Engine.desired_speed",
        "ns=2;i=10": "Power"
    }

    

    while True:
        try:
            for node_id, key in key_mappings.items():
                opcua_node = client.get_node(node_id)
                value = opcua_node.get_value()
                
                # Apply multiplier to desired speed
                if key == "World.PrimaryBattleship.Engine.desired_speed":
                    speed_multiplier = random.uniform(9.8, 10.4)
                    value *= speed_multiplier


                # Apply fluctuation to Power value
                if key == "Power":
                    value = apply_power_fluctuation(value)

                print(f"{key}: {value}")

                data = {key: value}
                data_out = json.dumps(data)
                mqtt_client.publish("v1/devices/me/telemetry", data_out, 0)

                # Debug Statement
                #ic(mqtt_client.publish("v1/devices/me/telemetry", data_out, 0))
            time.sleep(0.001)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()
