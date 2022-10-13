# -*- coding: utf-8 -*-
"""
Created on 2022-06-14

@author: ivespe

Test script for simple analyses using the CINELDI MV reference system. 

TODO: creating an "extended" version of the CINELDI reference system (as opposed to the 
"base" version representing the present-day distribution system) for a specific stage of a 
load development scenario.
"""

# %% Set-up for script

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

# Scenario file name 
# (NB: For the published version of the reference data set, it is assumed that new loads
# are LECs that will be associated with primarily residential load time series)
filename_scenario = 'scenario_LEC_only.csv'

# File name of 24-hour load time series (profiles) for charging stations
# (NB: Not included with the published version of the reference data set)
filename_load_profiles_cs = 'load_profiles_charging_stations.csv'

filename_residential_fullpath = os.path.join(path_data_set,'load_time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'load_time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_time_series_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_scenario_fullpath = os.path.join(path_data_set,filename_scenario)
filename_load_profiles_cs_fullpath = os.path.join(path_data_set,filename_load_profiles_cs)

# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %% Read scenario data

scen = ls.read_scenario_from_csv(path_data_set,filename_point_load = filename_scenario)

# %% Apply scenario data to network

# Year in the analysis horizon relative to the reference year (2021)
year_rel = 7

ls.apply_scenario_to_net(net,scen,year_rel)

# %% Test running power flow with a peak load model
# (i.e., all loads are assumed to be at their annual peak load simultaneously)

pp.runpp(net,init='results',algorithm='bfsw')

print('Total load demand in the system assuming a peak load model: ' + str(net.res_load['p_mw'].sum()) + ' MW')

# %% Plot results of power flow calculations

pp_plotting.pf_res_plotly(net)

# %% Set up hourly normalized load time series for a representative day (28 February by default)

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Get relative load profiles for representative days mapped to buses of the CINELDI test network
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_data_fullpath,filename_scenario_fullpath,filename_load_mapping_fullpath,filename_load_profiles_cs_fullpath)

# %% Scale loads by normalized load time series and run power flow

# Which hour of the representative day to investigate (0-indexed). By default investigate the peak-load hour of February 28. 
# (NB: It is necessary to reload the pandapower network and reapply the scenario data before investigating another value of t)
t = 19

for i in net.load.index:
    net.load.loc[i,'scaling'] = profiles_mapped.loc[t,i]

pp.runpp(net,init='results',algorithm='bfsw')

print('Total load demand in the system assuming a time-varying load model with a representative day: ' + str(net.res_load['p_mw'].sum()) + ' MW')

# %% Plot power flow solution for time-varying load model

pp_plotting.pf_res_plotly(net)
# %%