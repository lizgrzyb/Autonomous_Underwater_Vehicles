#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUB.py:

Class for a submarine based on simplified hydrodynamic dynamics.
The submarine model focuses on controlling surge, heave, and pitch, while
ignoring sway, roll, and yaw. This code is derived from remus100.py with
necessary adaptations for submarine-specific dynamics.

SUB('depthHeadingAutopilot', z_d, theta_d, V_c, beta_c)
z_d: desired depth (m), positive downwards
theta_d: desired pitch angle (deg)
V_c: current speed (m/s)
beta_c: current direction (deg)
Methods:
dynamics(), depthAutopilot(), pitchAutopilot(), depthHeadingAutopilot(), stepInput()

"""

import numpy as np
import math
import sys
from BattleshipSimulator.python_vehicle_simulator.lib.control import PIDpolePlacement
from BattleshipSimulator.python_vehicle_simulator.lib.gnc import crossFlowDrag, forceLiftDrag, Hmtrx, m2c, gvect, ssa

# Class Vehicle
class SUB:
"""
SUB()
Step inputs, depth, and heading autopilot for a simplified submarine model.

SUB('depthHeadingAutopilot', z_d, theta_d, V_c, beta_c)
Depth and pitch autopilot.

Inputs:
z_d: desired depth (m)
theta_d: desired pitch angle (deg)
V_c: current speed (m/s)
beta_c: current direction (deg)
"""

def __init__(
self,
controlSystem="stepInput",
r_z=0,
r_theta=0,
V_current=0,
beta_current=0,
):
# Constants
self.D2R = math.pi / 180 # deg2rad
self.rho = 1025 # density of seawater (kg/m^3)
g = 9.81 # gravity (m/s^2)

if controlSystem == "depthHeadingAutopilot":
self.controlDescription = (
"Depth and pitch autopilot, z_d = "
+ str(r_z)
+ ", theta_d = "
+ str(r_theta)
+ " deg"
)
else:
self.controlDescription = "Step input for thrust and pitch"
controlSystem = "stepInput"

self.ref_z = r_z
self.ref_theta = r_theta
self.V_c = V_current
self.beta_c = beta_current * self.D2R
self.controlMode = controlSystem

# Initialize the submarine model
self.name = "Submarine Model (adapted from remus100)"
self.L = 6.0 # length (m)
self.B = 0.75 # beam (m)
self.T = 0.4 # draft (m)
self.mass = self.rho * self.L * self.B * self.T * 0.6 # approximate mass

# Velocity and control input vectors for surge, heave, pitch
self.nu = np.array([0, 0, 0, 0, 0, 0], float) # [u, v, w, p, q, r]
self.u_actual = np.array([0, 0, 0], float) # [thrust, pitch control, n]

self.controls = ["Surge thrust (N)", "Heave force (N)", "Pitch moment (Nm)"]
self.dimU = len(self.controls)

# Actuator dynamics
self.T_thrust = 1.0 # thrust time constant (s)
self.T_pitch = 1.0 # pitch time constant (s)

# Hydrodynamics (Fossen, 2021)
self.CD_0 = 0.08 # parasitic drag coefficient for surge
self.CL_delta_s = 0.7 # lift coefficient for stern plane

# Inertia properties
self.I_y = 5500 # Moment of inertia about y-axis (kg·m²)
self.mass = self.rho * self.L * self.B * self.T

# Define other needed constants for the model (heave and surge)
self.Kp_z = 0.1 # PID gain for depth (z-axis)
self.Kp_theta = 1.0 # PID gain for pitch (theta-axis)

# Control system settings
self.z_int = 0 # depth integral state
self.theta_int = 0 # pitch integral state

def dynamics(self, eta, nu, u_actual, u_control, sampleTime):
"""
[nu, u_actual] = dynamics(eta, nu, u_actual, u_control, sampleTime)
integrates the submarine equations of motion using Euler's method.
"""
# Current velocities in water
u_c = self.V_c * math.cos(self.beta_c - eta[5]) # current surge velocity
nu_c = np.array([u_c, 0, 0, 0, 0, 0], float) # current velocity vector
nu_r = nu - nu_c # relative velocity vector

# Control forces and moments (surge, heave, pitch)
tau_surge = u_control[0] # surge thrust (N)
tau_pitch = u_control[2] # pitch moment (Nm)

# Hydrodynamic drag in surge and pitch
C_x = -self.CD_0 * self.mass
M_q = -0.05 * self.I_y # pitch damping

# Control forces vector [surge force, heave force, pitch moment]
tau = np.array([tau_surge - C_x * nu_r[0], 0, tau_pitch - M_q * nu_r[4]], float)

# Inertia matrix for surge and pitch
M = np.diag([self.mass, self.mass, self.mass, 0, self.I_y, 0])
Minv = np.linalg.inv(M)

# Calculate the rate of change in velocities
nu_dot = np.matmul(Minv, tau)

# Forward Euler integration for velocity updates
nu = nu + sampleTime * nu_dot

# Update control inputs (thrust and pitch)
u_actual = u_control

return nu, u_actual

def depthAutopilot(self, eta, nu, sampleTime):
"""
u_control = depthAutopilot(eta, nu, sampleTime)
PID controller for automatic depth control.
"""
z = eta[2] # current depth (heave position)
w = nu[2] # heave rate
e_z = self.ref_z - z # depth tracking error

# PID controller for depth
[u_depth, self.z_int, self.ref_z] = PIDpolePlacement(
self.z_int, e_z, -w, self.ref_z, 0, 0,
self.mass, self.Kp_z, 1, sampleTime
)

return np.array([self.tau_X, u_depth, 0], float)

def pitchAutopilot(self, eta, nu, sampleTime):
"""
u_control = pitchAutopilot(eta, nu, sampleTime)
PID controller for automatic pitch control.
"""
theta = eta[4] # current pitch angle
q = nu[4] # pitch rate
e_theta = self.ref_theta * self.D2R - theta # pitch angle error

# PID controller for pitch
[u_pitch, self.theta_int, self.ref_theta] = PIDpolePlacement(
self.theta_int, e_theta, -q, self.ref_theta, 0, 0,
self.I_y, self.Kp_theta, 1, sampleTime
)

return np.array([self.tau_X, 0, u_pitch], float)

def depthHeadingAutopilot(self, eta, nu, sampleTime):
"""
u_control = depthHeadingAutopilot(eta, nu, sampleTime)
Combined depth and pitch control system.
"""
u_depth = self.depthAutopilot(eta, nu, sampleTime)[1]
u_pitch = self.pitchAutopilot(eta, nu, sampleTime)[2]

return np.array([self.tau_X, u_depth, u_pitch], float)

def stepInput(self, t):
"""
u = stepInput(t) generates simple surge thrust inputs.
"""
thrust = 10000 # N

if t > 50:
thrust = 0

return np.array([thrust, 0, 0], float)