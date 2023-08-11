# -*- coding: utf-8 -*-
"""
Created on 2022-12-04

@author: ivespe

Script for creating a version of the grid data set for a certain operating state, 
obtained for a "snapshot" for a given day and hour of the year from the load demand time series
"""

# %% Dependencies

import pandapower as pp
import pandas as pd
import os
import load_profiles as lp
import pandapower_read_csv as ppcsv

# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

# Filename of bus matrix on the MATPOWER format with load demand values for a given snapshot 
# (day and hour of the year) from the load demand data set; this output file will be saved to 
# the folder containing the code and not to the folder containing the (input) data set
filename_bus_snapshot = 'CINELDI_MV_reference_grid_snapshot_bus.csv'

# Scenario file name 
# (NB: For the published version of the reference data set, it is assumed that new loads
# are LECs that will be associated with primarily residential load time series)
filename_scenario = 'scenario_LEC_only.csv'

filename_bus = 'CINELDI_MV_reference_grid_base_bus.csv'
filename_bus_fullpath = os.path.join(path_data_set,filename_bus)
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_scenario_fullpath = os.path.join(path_data_set,filename_scenario)

# %% Read bus data for the base reference grid model

bus = pd.read_csv(filename_bus_fullpath, sep=';', decimal='.')
bus.set_index('bus_i',inplace=True,drop=True)

# %% Set up hourly normalized load time series for the full year

# Initialize load profile object 
load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Select the 28th of February (the peak load day in the system); the days are 1-indexed
day = 29*2+1

# Select the hour from 19:00 to 20:00 (the peak load hour in the peak load day); the hours are 0-indexed
hour = 19

# Get relative load profiles for representative days mapped to buses of the CINELDI test network;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,[day])

# %% Scale the load in the grid by the value of the normalized load time series

for bus_ID in profiles_mapped.columns:
    bus.loc[bus_ID,'Pd'] = bus.loc[bus_ID,'Pd'] * profiles_mapped.loc[hour,bus_ID]
    bus.loc[bus_ID,'Qd'] = bus.loc[bus_ID,'Qd'] * profiles_mapped.loc[hour,bus_ID]

# %% Write updated bus matrix to file

bus.to_csv(filename_bus_snapshot, sep = ';', decimal = '.', index = True)
# %%
