import math
import random
import uuid

def calculate_power(speed_mps, mode, beam_ft=34, drag_coeff=0.25, efficiency=0.75):
    ############################################################################################
    # This function only needs to take in the current speed of the ship for calculation.
    # The input speed currently expects meters/second
    # All calculations are based on "Marine Propellors and Propulsion" by John Carlton, 2018
    # Dimensions and information on Virginia class sub are from:
    # [1] U.S. Navy, "Attack Submarines (SSN)," [Online]. Available: https://www.navy.mil/Resources/Fact-Files/Display-FactFiles/Article/2169558/attack-submarines-ssn/. [Accessed: Nov. 24, 2024].
    # [2] Submarine Industrial Base Council, "Virginia Class," [Online]. Available: https://submarinesuppliers.org/programs/ssn-ssgn/virginia-class/. [Accessed: Nov. 24, 2024].
    ############################################################################################

    #Constants
    water_density = 1025 #kg/m^3
    beam_width_m = beam_ft* 0.3048
    area = math.pi * (beam_width_m / 2) ** 2

    #Calculating power:
    power_watts = (0.5 * water_density * area * drag_coeff * speed_mps ** 3)/efficiency #in watts

    #Additional fluctuation of +/-20% if attack is selected
    if mode==1:
        fluctuation = random.uniform(-0.2, 0.2)
        power_watts *= (1 + fluctuation)
    
    power_mw = power_watts / 1e6 #in megawatts

    return power_mw

###### EXAMPLE USE #######
#Opperation Modes
NORMAL = 0
POWER_ATTACK = 1
mode = POWER_ATTACK #set opperation to normal

#configuring seed:
seed = int(uuid.uuid4().int % (2**32))  # Limit to 32-bit integer for compatibility
random.seed(seed)  # Use system time to initialize the random seed

#setting constants and calling function
speed_mps = 12.86  # Example speed in m/s
power = calculate_power(speed_mps, mode)
print(power)



