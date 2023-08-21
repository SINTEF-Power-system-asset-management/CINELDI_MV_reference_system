# -*- coding: utf-8 -*-
"""
Created on 2023-07-13

@author: ivespe

Intro script for warm-up exercise ("exercise 0") in specialization course module 
"Flexibility in power grid operation and planning" at NTNU (TET4565/TET4575) 
"""

# %% Dependencies

import pandapower as pp
import pandapower.plotting as pp_plotting
import pandas as pd
import os
import load_scenarios as ls
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import matplotlib as mpl
import math

# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

filename_residential_fullpath = os.path.join(path_data_set,'time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')

# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %% Test running power flow with a peak load model
# (i.e., all loads are assumed to be at their annual peak load simultaneously)

pp.runpp(net,init='results',algorithm='bfsw')

print('Total load demand in the system assuming a peak load model: ' + str(net.res_load['p_mw'].sum()) + ' MW')

# %% Plot results of power flow calculations

pp_plotting.pf_res_plotly(net)

# %%
