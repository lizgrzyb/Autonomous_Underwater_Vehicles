#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control methods.

Reference: T. I. Fossen (2021). Handbook of Marine Craft Hydrodynamics and
Motion Control. 2nd. Edition, Wiley. 
URL: www.fossen.biz/wiley

Author:     Thor I. Fossen
"""

import numpy as np
from BattleshipSimulator.python_vehicle_simulator.lib.guidance import refModel3
from BattleshipSimulator.python_vehicle_simulator.lib.gnc import ssa, Rzyx

# SISO PID pole placement
def PIDpolePlacement(
    e_int,
    e_x,
    e_v,
    x_d,
    v_d,
    a_d,
    m,
    d,
    k,
    wn_d,
    zeta_d,
    wn,
    zeta,
    r,
    v_max,
    sampleTime,
):

    # PID gains based on pole placement
    Kp = m * wn ** 2 - k
    Kd = m * 2 * zeta * wn - d
    Ki = (wn / 10) * Kp

    # PID control law
    u = -Kp * e_x - Kd * e_v - Ki * e_int

    # Integral error, Euler's method
    e_int += sampleTime * e_x

    # 3rd-order reference model for smooth position, velocity and acceleration
    [x_d, v_d, a_d] = refModel3(x_d, v_d, a_d, r, wn_d, zeta_d, v_max, sampleTime)

    return u, e_int, x_d, v_d, a_d


# MIMO nonlinear PID pole placement
def DPpolePlacement(
    e_int, M3, D3, eta3, nu3, x_d, y_d, psi_d, wn, zeta, eta_ref, sampleTime
):

    # PID gains based on pole placement
    Kp = wn @ wn @ M3
    Kd = 2.0 * zeta @ wn @ M3 - D3
    Ki = (1.0 / 10.0) * wn @ Kp

    # DP control law - setpoint regulation
    e = eta3 - eta_ref
    e[2] = ssa(e[2])
    R = Rzyx(0.0, 0.0, eta3[2])
    tau = (
        -np.matmul((R.T @ Kp), e)
        - np.matmul((R.T @ Kd @ R), nu3)
        - np.matmul((R.T @ Ki), e_int)
    )

    # Low-pass filters, Euler's method
    T = 5.0 * np.array([1 / wn[0][0], 1 / wn[1][1], 1 / wn[2][2]])
    x_d += sampleTime * (eta_ref[0] - x_d) / T[0]
    y_d += sampleTime * (eta_ref[1] - y_d) / T[1]
    psi_d += sampleTime * (eta_ref[2] - psi_d) / T[2]

    # Integral error, Euler's method
    e_int += sampleTime * e

    return tau, e_int, x_d, y_d, psi_d

def integralSMC(
    e_int,
    e_x,
    e_v,
    x_d,
    v_d,
    a_d,
    T_nomoto,
    K_nomoto,
    wn_d,
    zeta_d,
    K_d,
    K_sigma,
    lam,
    phi_b,
    r,
    v_max,
    sampleTime,
):

    # Sliding surface
    v_r_dot = a_d - 2 * lam * e_v - lam ** 2 * ssa(e_x)
    v_r     = v_d - 2 * lam * ssa(e_x) - lam ** 2 * e_int
    sigma   = e_v + 2 * lam * ssa(e_x) + lam ** 2 * e_int

    #  Control law
    if abs(sigma / phi_b) > 1.0:
        delta = ( T_nomoto * v_r_dot + v_r - K_d * sigma 
                 - K_sigma * np.sign(sigma) ) / K_nomoto
    else:
        delta = ( T_nomoto * v_r_dot + v_r - K_d * sigma 
                 - K_sigma * (sigma / phi_b) ) / K_nomoto

    # Integral error, Euler's method
    e_int += sampleTime * ssa(e_x)

    # 3rd-order reference model for smooth position, velocity and acceleration
    [x_d, v_d, a_d] = refModel3(x_d, v_d, a_d, r, wn_d, zeta_d, v_max, sampleTime)

    return delta, e_int, x_d, v_d, a_d


# CIP begin
# SISO PID pole placement for surge and heave control
def CIPPIDpolePlacement(
    e_int,
    e_x,
    e_v,
    x_d,
    v_d,
    a_d,
    m,
    wn,
    zeta,
    sampleTime,
    B=10880,  # Buoyancy force (placeholder)
    C_x=0.1,  # Drag coefficient in x-direction (placeholder)
):
 
    # PID gains based on pole placement
    Kp = m * wn ** 2.0
    Kd = m * 2.0 * zeta * wn
    Ki = (wn / 10.0) * Kp
 
    # Submarine-specific control law (including buoyancy and drag)
    u = -Kp * e_x - Kd * e_v - Ki * e_int + B - (C_x * e_v)
 
    # Integral error update using Euler's method
    e_int += sampleTime * e_x
 
    # Smooth position, velocity, and acceleration using refModel3
    x_d, v_d, a_d = refModel3(x_d, v_d, a_d, e_x, wn, zeta, 10880, sampleTime)
 
    return u, e_int, x_d, v_d, a_d


# MIMO nonlinear PID pole placement for heave and pitch control
def CIPDPpolePlacement(
    e_int, M2, D2, eta2, nu2, x_d, z_d, theta_d, wn, zeta, sampleTime,
    B=10880,  # Buoyancy force (placeholder)
    I_y=5500,  # Moment of inertia in y-axis (placeholder)
    C_z=0.1,  # Drag coefficient in z-direction (placeholder)
):
 
    # Submarine-specific PID gains based on pole placement for heave and pitch
    M2_diag = np.diag(np.diag(M2))
    D2_diag = np.diag(np.diag(D2))
    
    Kp = wn @ wn @ M2_diag
    Kd = 2.0 * zeta @ wn @ M2_diag - D2_diag
    Ki = (1.0 / 10.0) * wn @ Kp
 
    # Adjusting control for heave and pitch
    e = eta2 - np.array([x_d, z_d, theta_d])
    e[2] = ssa(e[2])  # Smallest-signed angle adjustment for pitch error
    R = Rzyx(eta2[2])  # 2D rotation matrix for pitch
 
    # Modified control law for submarine heave and pitch
    tau = (
        - np.matmul((R.T @ Kp), e)
        - np.matmul(Kd, nu2)
        - np.matmul((R.T @ Ki), e_int)
        + B * np.cos(theta_d)  # Buoyancy effect for pitch
        - C_z * nu2[1]  # Drag effect in the z-direction
    )
 
    # Low-pass filters for heave and pitch control, Euler's method
    T = 5.0 * np.array([1 / wn[0][0], 1 / wn[1][1], 1 / wn[2][2]])
    x_d += sampleTime * (eta2[0] - x_d) / T[0]
    z_d += sampleTime * (eta2[1] - z_d) / T[1]
    theta_d += sampleTime * (eta2[2] - theta_d) / T[2]
 
    # Integral error update using Euler's method
    e_int += sampleTime * e
 
    return tau, e_int, x_d, z_d, theta_d
# CIP end

