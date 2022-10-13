"""
Created on 2022-01-27

@author: ivespe

Script for creating mapping between the 104 load time series (load IDs) in the load data set
and bus IDs of the 124-bus CINELDI MV reference grid.
"""

# %% Dependencies

import pandas as pd
import os
import pandapower_read_csv as ppcsv
import load_scenarios as ls

# %% Set up paths

# Location of orignal load data set
path_input = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/load_data_input/'

# Location of (processed) data set for CINELDI MV reference system
path_data_set = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

# Scenario file name 
# (NB: Assuming that new loads are LECs that will be associated with primarily residential load time series)
filename_scenario = 'scenario_LEC_only.csv'

filename_residential_fullpath = os.path.join(path_data_set,'time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_output_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')

# %% Read input data

df_load_IDs_irregular = pd.read_csv(filename_irregular_fullpath,sep=';')    
df_load_IDs_residential = pd.read_csv(filename_residential_fullpath,sep=';')
load_data = pd.read_csv(filename_load_data_fullpath,sep=';')
load_data.set_index('Time',inplace = True)

# Read grid data
net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# Read load scenarios
scen = ls.read_scenario_from_csv(path_data_set,filename_point_load = filename_scenario)

# %% Create load mapping

# We will be working with lists to use set operations easily
load_IDs_irregular = df_load_IDs_irregular['time_series_ID'].to_list()
load_IDs_residential = df_load_IDs_residential['time_series_ID'].to_list()

# Load IDs in the load data set
load_IDs_load_data = list([int(col_name) for col_name in load_data.columns])

load_IDs_regular = list(set(load_IDs_load_data) - set(load_IDs_irregular))

# Bus numbers for the buses that have a load point in the load data set
bus_IDs_network = net.load['bus'].to_list()

# Bus numbers of new buses with residential loads that are potential LECs
bus_ID_LEC = list(scen['point_loads']['bus_i'].unique())

# First to mapping for the potential new (residential) loads in the network
mapping_new_load_to_bus = pd.DataFrame(index = bus_ID_LEC, columns = ['time_series_ID', 'existing_load'])
i_residential = 0
for bus_ID in bus_ID_LEC:
    mapping_new_load_to_bus.loc[bus_ID,'time_series_ID'] = load_IDs_residential[i_residential]
    mapping_new_load_to_bus.loc[bus_ID,'existing_load'] = False
    i_residential += 1

# The regular loads left to map to the network (excluding already mapped residential loads)
load_IDs_regular_left = list( set(load_IDs_regular) - set(load_IDs_residential[:i_residential])  )

# Then map as many are needed of the remaining loads to buses in the network
mapping_load_to_bus = pd.DataFrame(index = bus_IDs_network, columns = ['time_series_ID'])
i_regular_left = 0
for bus_ID in bus_IDs_network:
    mapping_load_to_bus.loc[bus_ID,'time_series_ID'] = load_IDs_regular_left[i_regular_left]
    mapping_load_to_bus.loc[bus_ID,'existing_load'] = True
    i_regular_left += 1

# Include both existing and potential new loads in the mapping
mapping_load_to_bus = pd.concat([mapping_load_to_bus, mapping_new_load_to_bus],axis = 0)
mapping_load_to_bus.index.name = 'bus_i'


# %% Write mapping between load profiles and test network buses to file

mapping_load_to_bus.to_csv(filename_load_mapping_output_fullpath, sep = ';', decimal = '.')

# %%
