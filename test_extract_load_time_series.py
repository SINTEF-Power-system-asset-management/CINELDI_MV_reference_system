# -*- coding: utf-8 -*-
"""
Created on 2022-11-30

@author: ivespe

Script for extracting load time series in units MWh/h for existing load points in the CINELDI reference grid
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
path_data_set = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

# Scenario file name 
# (NB: For the published version of the reference data set, it is assumed that new loads
# are LECs that will be associated with primarily residential load time series)
filename_scenario = 'scenario_LEC_only.csv'

filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_scenario_fullpath = os.path.join(path_data_set,filename_scenario)

# %% Read grid data

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %% Set up hourly normalized load time series for the full year

# Initialize load profile object 
load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Get all the days of the year
repr_days = list(range(1,366))

# Get relative load profiles for representative days mapped to buses of the CINELDI test network;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# %% Calculate load time series in units MW (or, equivalently, MWh/h)

# Scale the normalized load time series by the peak load value for the load points in the grid data set (in units MW);
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])

# Remove the columns corresponding to buses that do not have load points in the existing grid
# (since the load mapping also includes the buses for potential new load points for local energy communities)
load_time_series_mapped.dropna(axis=1,inplace=True)