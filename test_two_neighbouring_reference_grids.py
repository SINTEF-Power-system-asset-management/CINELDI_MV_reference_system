# -*- coding: utf-8 -*-
"""
Created on 2023-03-01

@author: ivespe

Test script for duplicating the reference system to simulate two neighbouring 124-bus grids
"""

# %% Dependencies

import pandapower as pp
import pandapower.plotting as pp_plotting
import pandas as pd
import os
import CINELDI_MV_reference_system.load_scenarios as ls
import CINELDI_MV_reference_system.load_profiles as lp
import CINELDI_MV_reference_system.pandapower_read_csv as ppcsv

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

filename_residential_fullpath = os.path.join(path_data_set,'time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_scenario_fullpath = os.path.join(path_data_set,filename_scenario)
filename_load_profiles_cs_fullpath = os.path.join(path_data_set,filename_load_profiles_cs)

# %%

net_1 = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)
net_2 = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# List with indices of the days of the year to extract load profiles for (1-indexed; 28 February by default)
repr_days = [31+28]

# Get relative load profiles for representative days mapped to buses of the CINELDI test network
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_data_fullpath,filename_scenario_fullpath,filename_load_mapping_fullpath,filename_load_profiles_cs_fullpath,repr_days)

# Which hour of the representative day to investigate (0-indexed). By default investigate the peak-load hour of February 28. 
# (NB: It is necessary to reload the pandapower network and reapply the scenario data before investigating another value of t)
t = 19

# Scale loads by normalized load time series and run power flow
for i in net_1.load.index:
    net_1.load.loc[i,'scaling'] = profiles_mapped.loc[t,i]
for i in net_2.load.index:
    net_2.load.loc[i,'scaling'] = profiles_mapped.loc[t,i]

for bus_id in net_1.bus.index:
    net_1.bus.loc[bus_id,'name'] = str(net_1.bus.loc[bus_id,'name']) + '-A'
for bus_id in net_2.bus.index:
    net_2.bus.loc[bus_id,'name'] = str(net_2.bus.loc[bus_id,'name']) + '-B'

net_extended = pp.merge_nets(net_1,net_2)

bf_A = 62
bt_B = 36

#bus_id_A = net_extended.bus[net_extended.bus['name'] == '62-A'].index[0]

#pp.create_switch(net_extended,bf_1,bf_2+124,'b')
pp.create_line_from_parameters(net_extended,bf_A,bt_B+124,0.1,net_1.line.loc[0,'r_ohm_per_km'],net_1.line.loc[0,'x_ohm_per_km'],net_1.line.loc[0,'c_nf_per_km'],net_1.line.loc[0,'max_i_ka'])
pp.runpp(net_extended,init='auto',algorithm='nr')
pp_plotting.pf_res_plotly(net_extended)

print('Total load demand in the system assuming a time-varying load model with a representative day: ' + str(net_extended.res_load['p_mw'].sum()) + ' MW')

net_extended.line.loc[12,'in_service'] = False
pp.runpp(net_extended,init='auto',algorithm='nr')
pp_plotting.pf_res_plotly(net_extended)


# %


# %%

