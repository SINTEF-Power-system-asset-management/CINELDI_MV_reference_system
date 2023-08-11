# -*- coding: utf-8 -*-
"""
Created on 2023-08-07

@author: ivespe

Test script for mapping load time series to the grid model including additional load profiles for charging stations
(not included with the published version of the reference data set; without this file, this script will crash). 
"""

# %% Dependencies

import pandapower as pp
import pandapower.plotting as pp_plotting
import pandas as pd
import os
import load_scenarios as ls
import load_profiles as lp
import pandapower_read_csv as ppcsv

# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

# Scenario file name including two LECs
filename_scenario = 'scenario_LEC_and_FCS.csv'

# File name of 24-hour load time series (profiles) for charging stations
# (NB: Not included with the published version of the reference data set)
filename_load_profiles_cs = 'load_profiles_charging_stations.csv'

filename_residential_fullpath = os.path.join(path_data_set,'time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_scenario_fullpath = os.path.join(path_data_set,filename_scenario)
filename_load_profiles_cs_fullpath = os.path.join(path_data_set,filename_load_profiles_cs)

# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %% Read scenario data

scen = ls.read_scenario_from_csv(path_data_set,filename_point_load = filename_scenario)

# %% Set up hourly normalized load time series for a representative day 

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# List with indices of the days of the year to extract load profiles for (1-indexed; 28 February by default)
repr_days = [31+28]

# Get relative load profiles for representative days mapped to buses of the CINELDI test network
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# %% Add load profiles for charging stations to the mapping

profiles_mapped = load_profiles.map_cs_load_profiles(profiles_mapped,filename_scenario_fullpath,filename_load_profiles_cs_fullpath)

# %%
