# -*- coding: utf-8 -*-
"""
Created on 2023-07-14

@author: ivespe

Intro script for Exercise 2 ("Load modelling to evaluate the need for flexibility") 
in specialization course module "Flexibility in power grid operation and planning" 
at NTNU (TET4565/TET4575) 

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


# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

# Scenario file name 
# (NB: For the published version of the reference data set, it is assumed that new loads
# are LECs that will be associated with primarily residential load time series)
filename_scenario = 'scenario_LEC_only.csv'

filename_residential_fullpath = os.path.join(path_data_set,'time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_scenario_fullpath = os.path.join(path_data_set,filename_scenario)

# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %% Set up hourly normalized load time series for a representative day 

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Get all the days of the year
repr_days = list(range(1,366))

# Get relative load profiles for representative days mapped to buses of the CINELDI reference grid;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_data_fullpath,filename_scenario_fullpath,filename_load_mapping_fullpath,None,repr_days)

# %% Calculate load time series in units MW (or, equivalently, MWh/h)

# Scale the normalized load time series by the peak load value for the load points in the grid data set (in units MW);
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])