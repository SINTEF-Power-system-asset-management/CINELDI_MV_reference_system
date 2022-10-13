"""
Created on 2022-10-05

@author: ivespe

Script for preparing data for reliability analysis (load point data and component reliability data) 
for the CINELDI MV reference system.
"""

# %% Dependencies

import pandas as pd
import os

# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

# Input file names
filename_line_types = 'distribution_line_types_in_reference_grid.csv'
filename_reldata_input = 'reldata_for_component_types.csv'
filename_bus = 'CINELDI_MV_reference_grid_base_bus.csv'
filename_branch = 'CINELDI_MV_reference_grid_base_branch.csv'
filename_branch_extra = 'CINELDI_MV_reference_grid_base_branch_extra.csv'
filename_share_load = 'share_load_per_customer_type.csv'
filename_mapping_load = 'mapping_loads_to_CINELDI_MV_reference_grid.csv'
filename_load_data = 'load_data_CINELDI_MV_reference_system.csv'

# Output file names
filename_reldata_output = 'CINELDI_MV_reference_system_reldata.csv'
filename_load_point_data = 'CINELDI_MV_reference_system_load_point.csv'
filename_customer_type_data = 'customer_interruption_cost_data.csv'

# Set default sectioning time (hours)
sectioning_time = 0.5

# %% Load input data

filename_reldata_input_fullpath = os.path.join(path_data_set,filename_reldata_input)
filename_bus_fullpath = os.path.join(path_data_set,filename_bus)
filename_branch_fullpath = os.path.join(path_data_set,filename_branch)
filename_branch_extra_fullpath = os.path.join(path_data_set,filename_branch_extra)
filename_line_types_fullpath = os.path.join(path_data_set,filename_line_types)
filename_share_load_fullpath = os.path.join(path_data_set,filename_share_load)
filename_mapping_load_fullpath = os.path.join(path_data_set,filename_mapping_load)
filename_load_data_fullpath = os.path.join(path_data_set,filename_load_data)

reldata_input = pd.read_csv(filename_reldata_input_fullpath, sep=';')
reldata_input.set_index('main_type',drop=True,inplace=True)
bus = pd.read_csv(filename_bus_fullpath, sep=';')
bus.set_index('bus_i',drop=True,inplace=True)
branch = pd.read_csv(filename_branch_fullpath, sep=';')
branch_extra = pd.read_csv(filename_branch_extra_fullpath, sep=';')
line_types = pd.read_csv(filename_line_types_fullpath, sep=';')
line_types.set_index('type',drop=True,inplace=True)
share_load = pd.read_csv(filename_share_load_fullpath, sep=';')
share_load.drop(columns = ['time_series_ID'],inplace=True)
mapping_load = pd.read_csv(filename_mapping_load_fullpath, sep=';')
mapping_load.set_index('bus_i',drop=False,inplace=True)
load_data = pd.read_csv(filename_load_data_fullpath, sep=';')


# %% Calculate line reliability data

# Initialize output DataFrame
reldata = pd.DataFrame(index = branch_extra.index, columns = ['f_bus', 't_bus', 'lambda_perm', 'lambda_temp', 'r_perm', 'r_temp', 'sectioning_time'])

for i_branch in branch_extra.index:
    type = branch_extra.loc[i_branch,'type']
    f_bus = branch.loc[i_branch,'f_bus']
    t_bus = branch.loc[i_branch,'t_bus']
    main_type = line_types.loc[type,'main_type']
    length_km = branch_extra.loc[i_branch,'length_km']

    # Calculate failure frequencies from reliability statistics (which are reported per 100 km of line)
    lambda_perm_main_type = reldata_input.loc[main_type,'lambda_perm'] / 100
    lambda_temp_main_type = reldata_input.loc[main_type,'lambda_temp'] / 100
    lambda_perm = lambda_perm_main_type * length_km
    lambda_temp = lambda_temp_main_type * length_km

    # Find outage times from reliability statistics
    r_perm = reldata_input.loc[main_type,'r_perm'] 
    r_temp = reldata_input.loc[main_type,'r_temp'] 

    # Put values into the output DataFrame
    reldata.loc[i_branch,'f_bus'] = f_bus
    reldata.loc[i_branch,'t_bus'] = t_bus
    reldata.loc[i_branch,'lambda_perm'] = lambda_perm
    reldata.loc[i_branch,'lambda_temp'] = lambda_temp
    reldata.loc[i_branch,'r_perm'] = r_perm
    reldata.loc[i_branch,'r_temp'] = r_temp
    reldata.loc[i_branch,'sectioning_time'] = sectioning_time

# %% Set values for load point reliability data 

bus_IDs_load_points = mapping_load.loc[mapping_load['existing_load'],'bus_i'].tolist()

load_point_data = pd.DataFrame(index = bus_IDs_load_points, columns = ['bus_i', 'customer_type', 'P_ref_MW', 'P_avg_MW', 'ratio_P_ref_P_avg','c_NOK_per_kWh_1h','c_NOK_per_kWh_4h'])
load_point_data['bus_i'] = bus_IDs_load_points

for bus_i in load_point_data.index:
    # Find the dominant customer type for the load point
    time_series_ID = mapping_load.loc[bus_i,'time_series_ID']
    P_ref_MW = bus.loc[bus_i,'Pd']
    P_avg_MW = load_data[str(time_series_ID)].mean() * bus.loc[bus_i,'Pd']
    load_point_data.loc[bus_i,'P_avg_MW'] = P_avg_MW
    load_point_data.loc[bus_i,'customer_type'] = share_load.loc[time_series_ID].idxmax()
    load_point_data.loc[bus_i,'P_ref_MW'] = P_ref_MW
    load_point_data.loc[bus_i,'ratio_P_ref_P_avg'] = P_ref_MW / P_avg_MW

# %% Define cost functions for customer interruption costs

# Average consumer price index for the year that the customer cost functions are defined for (2017) 
# and for the reference year for the data set (2021) 
# (Source: https://www.ssb.no/priser-og-prisindekser/konsumpriser/statistikk/konsumprisindeksen)
KPI_2017 = 105.5
KPI_2021 = 116.1

# %% Prepare interruption cost data for each customer type

customer_types = pd.Index(name='customer_type', data=['residential','agriculture','public','industry','commercial'])
customer_type_data = pd.DataFrame(index = customer_types, columns = ['ratio_P_ref_P_avg','f_c','c_ref_1h','c_ref_4h'])

# Calculating typical P_ref / P_avg ratio for each customer type
for customer_type in customer_types:
    ratio_P_ref_P_avg = load_point_data.loc[load_point_data['customer_type'] == customer_type,'ratio_P_ref_P_avg'].mean()
    customer_type_data.loc[customer_type,'ratio_P_ref_P_avg'] = round(ratio_P_ref_P_avg,1)

# Inserting 2015 values for correction factors taken from Table I of G. H. Kjølle, I. B. Sperstad, and S. H. Jakobsen, 
# ‘Interruption costs and time dependencies in quality of supply regulation’, presented at the PMAPS 2014, Durham, 2014. 
# doi: 10.1109/PMAPS.2014.6960620.
customer_type_data.loc['residential','f_c'] = 0.96
customer_type_data.loc['agriculture','f_c'] = 0.88
customer_type_data.loc['public','f_c'] = 0.38
customer_type_data.loc['industry','f_c'] = 0.38
customer_type_data.loc['commercial','f_c'] = 0.49

# Specific interruption cost function evaluated for interruption duration r = 1 hour
# (Source: https://lovdata.no/forskrift/1999-03-11-302/§9-2)
r = 1
c_ref_1h_per_kW_2017 = pd.Series(index = customer_types, dtype='float64')
c_ref_1h_per_kW_2017['residential'] = 8.8 + 14.7*r
c_ref_1h_per_kW_2017['agriculture'] = 21.4+17.5*(r-1)
c_ref_1h_per_kW_2017['public'] = 194.5+31.4*(r-1)
c_ref_1h_per_kW_2017['industry'] = 132.6+92.5*(r-1)
c_ref_1h_per_kW_2017['commercial'] = 220.3+102.4*(r-1)

# Convert from cost level 2017 (in the current regulation) to cost level 2021
c_ref_1h_per_kW_2021 = c_ref_1h_per_kW_2017 * KPI_2021/KPI_2017
customer_type_data['c_ref_1h'] = c_ref_1h_per_kW_2021 

# Specific interruption cost function evaluated for interruption duration r = 4 hours
# (Source: https://lovdata.no/forskrift/1999-03-11-302/§9-2)
r = 4
c_ref_4h_per_kW_2017 = pd.Series(index = customer_types, dtype='float64')
c_ref_4h_per_kW_2017['residential'] = 38.4+21.9*(r-2)
c_ref_4h_per_kW_2017['agriculture'] = 74.2+16.1*(r-4)
c_ref_4h_per_kW_2017['public'] = 288.9+58.2*(r-4)
c_ref_4h_per_kW_2017['industry'] = 410.3+62.5*(r-4)
c_ref_4h_per_kW_2017['commercial'] = 527.2+158.8 *(r-4)

# Convert from cost level 2017 (in the current regulation) to cost level 2021
c_ref_4h_per_kW_2021 = c_ref_4h_per_kW_2017 * KPI_2021/KPI_2017
customer_type_data['c_ref_4h'] = c_ref_4h_per_kW_2021 


# %% Add specific interruption cost data (in NOK/kWh) to the load point data

for i_bus in load_point_data.index:
    customer_type = load_point_data.loc[bus_i,'customer_type']
    ratio_P_ref_P_avg = load_point_data.loc[i_bus,'ratio_P_ref_P_avg']
    f_c = customer_type_data.loc[customer_type,'f_c']
    
    c_ref_1h = customer_type_data.loc[customer_type,'c_ref_1h']
    c_NOK_per_kWh_1h = c_ref_1h/1 * f_c * ratio_P_ref_P_avg
    load_point_data.loc[i_bus,'c_NOK_per_kWh_1h'] = c_NOK_per_kWh_1h

    c_ref_4h = customer_type_data.loc[customer_type,'c_ref_4h']    
    c_NOK_per_kWh_4h = c_ref_4h/4 * f_c * ratio_P_ref_P_avg
    load_point_data.loc[i_bus,'c_NOK_per_kWh_4h'] = c_NOK_per_kWh_4h

# %% Write output to files

filename_reldata_output_fullpath = os.path.join(path_data_set,filename_reldata_output)
reldata.to_csv(filename_reldata_output_fullpath, sep = ';', index = False)

filename_load_point_data_fullpath = os.path.join(path_data_set,filename_load_point_data)
load_point_data.drop(columns = ['P_ref_MW','P_avg_MW','ratio_P_ref_P_avg'], inplace=True)
load_point_data.to_csv(filename_load_point_data_fullpath, sep = ';', index = False)

filename_customer_type_data_fullpath = os.path.join(path_data_set,filename_customer_type_data)
customer_type_data.to_csv(filename_customer_type_data_fullpath, sep = ';', index = True)

# %%
