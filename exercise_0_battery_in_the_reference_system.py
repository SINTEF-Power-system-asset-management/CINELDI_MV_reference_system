# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: title,-all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: cineldi-mv-reference-system (3.14.x)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Script for warm-up exercise ("exercise 0"): A battery in the grid
#
# Intro script for warm-up exercise ("exercise 0") in specialization course module 
# "Flexibility in power grid operation and planning" at NTNU (TET4565/TET4575) 

# %%
# Dependencies

import pandapower as pp
import pandapower.plotting as pp_plotting
import pandas as pd
import os
import load_scenarios as ls
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import matplotlib as mpl

# %%
# Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

filename_residential_fullpath = os.path.join(path_data_set,'time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')


# %%
# Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %%
# Test running power flow with a peak load model
# (i.e., all loads are assumed to be at their annual peak load simultaneously)

pp.runpp(net,init='results',algorithm='bfsw')

print('Total load demand in the system assuming a peak load model: ' + str(net.res_load['p_mw'].sum()) + ' MW')

# %%
# Plot results of power flow calculations

pp_plotting.pf_res_plotly(net)

# %%
# Calculate voltage profile

buses = []
voltage_profile = []

# Start from bus 96 (where we assume that a new customer will be connected)
next_bus = 96

# Trace the radial (tree graph) back to bus 1 (the main feeder HV/MV substation) 
while next_bus != 1:
    prev_bus = next_bus
    next_bus = min(list(pp.toolbox.get_connected_buses(net,next_bus)))
    U = net.res_bus.loc[prev_bus,'vm_pu']
    voltage_profile += [U]
    buses += [prev_bus]

# NB: Here we have not actually checked whether bus 96 is at the end of the radial

# %%
# Plot voltage profile

# Settings for plotting
mpl.rcParams.update({
    'font.family': 'Calibri',    #
    'font.size': 11,           #
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'lines.linewidth': 1.5,
    'axes.linewidth': 1,
    'grid.linewidth': 0.5,
    'legend.frameon': False
})
plt.rcParams['axes.grid'] = False
plt.rcParams['font.family'] = 'Calibri'

fig, ax = plt.subplots(figsize=(8, 4.5),dpi=600)
plt.plot(buses,voltage_profile, 'r')
plt.plot([buses[0], buses[-1]],[0.95, 0.95], 'k--')
ax.set_xlabel('Bus number')
ax.set_ylabel('Voltage (p.u.)')
plt.tight_layout()
plt.show()

print(f'Minimum voltage in grid: {min(voltage_profile):.4f} p.u.')

 # NB: We know that bus 96 has the lowest voltage value in the grid but we have not actually checked this in the code above

# %%
