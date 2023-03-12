"""
Created on 2022-01-27

@author: ivespe

Script for processing the CINELDI MV reference grid by adding charging susceptance 
based on standard line type information from Planleggingsbok for kraftnett and 
estimating line lengths. Also updating format of files to standard MATPOWER format.
"""

# %% Dependencies

import pandas as pd
import os
import math
import pandapower as pp
import pandapower_read_csv as ppcsv

# %% Set up paths and parameters

# Path of folder with grid data files to be processed (inputs)
path_input = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/grid_data_input'

#  Path of folder with processed grid data (outputs)
path_data_set = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system'

# True if rateA (branch flow limit) is in p.u. and should be converted to units MVA 
do_mult_rateA = True

# Decimal separator sign to expect when reading the grid data
decimal_sep_in = ','

# Decimal separator sign to use in the modified grid data
decimal_sep_out = '.'

# Bus voltage maximum and minumum values 
# (according to common Norwegian planning criterion for MV distribution grids)
Vmin = 0.95
Vmax = 1.05

# Set file name variables (constants)
filename_line_types = "distribution_line_types_in_reference_grid.csv"

# Installation year of distribution lines has been pre-processed separately from other (confidential) input data
filename_installation_year = 'CINELDI_MV_reference_grid_branch_installation_year.csv'

# Hard coding file names for CINELDI reference grid data (old naming)
filename_branch = 'Cineldi124Bus_Branch.csv'    
filename_bus = 'Cineldi124Bus_Busdata.csv'
filename_branch_extra = 'Cineldi124Bus_Branch_extra.csv'   

# Hard coding file names for CINELDI reference grid data (new naming)
filename_branch_new = 'CINELDI_MV_reference_grid_base_branch.csv'    
filename_bus_new = 'CINELDI_MV_reference_grid_base_bus.csv'
filename_bus_extra_new = 'CINELDI_MV_reference_grid_base_bus_extra.csv'
filename_branch_extra_new = 'CINELDI_MV_reference_grid_base_branch_extra.csv'
filename_branch_pf_solution_new = 'CINELDI_MV_reference_grid_base_branch_pf_sol.csv'
filename_Excel_new = 'CINELDI_MV_reference_grid_base.xls'

# Constructing full paths of input and output files
filename_line_types_fullpath = os.path.join(path_data_set,filename_line_types)
filename_installation_year_fullpath = os.path.join(path_input,filename_installation_year)
filename_branch_fullpath = os.path.join(path_input,filename_branch)    
filename_bus_fullpath = os.path.join(path_input,filename_bus)
filename_branch_out_fullpath = os.path.join(path_data_set,filename_branch_new)    
filename_bus_out_fullpath = os.path.join(path_data_set,filename_bus_new)
filename_bus_extra_out_fullpath = os.path.join(path_data_set,filename_bus_extra_new)
filename_branch_extra_out_fullpath = os.path.join(path_data_set,filename_branch_extra_new)
filename_branch_pf_solution_new_fullpath = os.path.join(path_data_set,filename_branch_pf_solution_new)
filename_Excel_out_fullpath = os.path.join(path_data_set,filename_Excel_new)

# %% Read input data

# Read standard cable type data
line_type_data = pd.read_csv(filename_line_types_fullpath, sep=';')

# Read grid data from .csv files
branch = pd.read_csv(filename_branch_fullpath, sep=';', decimal=decimal_sep_in)    
bus = pd.read_csv(filename_bus_fullpath, sep=';', decimal=decimal_sep_in)
df_installation_year = pd.read_csv(filename_installation_year_fullpath, sep=';', decimal=decimal_sep_in)

# %% Calculate branch susceptance (and branch length)

# Assuming the grid to be operated at frequency 50 Hz
f_hz = 50.0
omega = math.pi * f_hz  # 1/s

# Assuming the base power value to be 10 MVA
baseMVA = 10

# Create DataFrame for extra/custom/auxiliary data fields for branches
branch_extra = pd.DataFrame(columns = ['type','length_km','installation_year','location_type'], index = branch.index)

# Read line data (and we assume there are no transformers)
for i_branch in branch.index:
    f_bus = branch.loc[i_branch,'f_bus']
    rateA = branch.loc[i_branch,'rateA']
    r = branch.loc[i_branch,'r']
    x = branch.loc[i_branch,'x']
    
    # Converting line rating to units A from p.u. (in units of baseMVA)
    baseKV = bus.loc[f_bus,'baseKV']
    I_max = round(rateA * baseMVA / baseKV  / math.sqrt(3) * 1000)

    # Base impedance value (ohm)
    Zni = baseKV**2/baseMVA  
    r_ohm = r * Zni

    # Approximate the cable to be one of the standard cable types according to a given mapping
    ids_same_rating = line_type_data.index[line_type_data['Imax_A'] == I_max]

    if len(ids_same_rating) == 1:
        id_line_type = ids_same_rating[0]        
    
    elif len(ids_same_rating) > 1:
        line_type_R_over_X = line_type_data.loc[ids_same_rating,'R_ohm_per_km'] / line_type_data.loc[ids_same_rating,'X_ohm_per_km']            
        ids_same_R_over_X = line_type_R_over_X.index[round(line_type_R_over_X,2) == round(r/x,2)]
        if len(ids_same_R_over_X) == 1:
            id_line_type = ids_same_R_over_X[0]
        elif len(ids_same_R_over_X) == 0:
            print('Error for branch #', i_branch , ': No line types with the same rating and R/X value')
            exit()
        elif len(ids_same_R_over_X) > 0:
            print('Warning for branch #', i_branch , ': Multiple line types with the same rating and R/X value; choosing the first one')            
            id_line_type = ids_same_R_over_X[0]

    elif len(ids_same_rating) == 0:
        # If cable type is not defined (according to given mapping), assume it to be a fictitious 
        # cable of negligible length (corresponding to the last entry in line_type_data)
        id_line_type = len(line_type_data.index)-1

    # Installation year of line
    installation_year = df_installation_year.loc[i_branch,'installation_year']

    # Identifier/name of the line type                    
    type_line = line_type_data.loc[id_line_type,'type']

    # Calculating length of cable
    r_ohm_per_km = line_type_data.loc[id_line_type,'R_ohm_per_km']
    length_km = r_ohm / r_ohm_per_km

    # Finding charging susceptance from standard cable type data ("driftskapasitet", Cd, in μf_per_km)
    c_μf_per_km = line_type_data.loc[id_line_type,'Cd_nF_per_km'] / 1000

    # Converting charging susceptance from μF (per km) to p.u.
    c_μf = c_μf_per_km * length_km 
    b = 2*omega*Zni*c_μf/1e6 
    branch.loc[i_branch,'b'] = b

    if do_mult_rateA:
        # Convert branch rating from p.u. to units MVA
        branch.loc[i_branch,'rateA'] = rateA * baseMVA

    # Add information to branch extra data fields
    branch_extra.loc[i_branch,'length_km'] = length_km
    branch_extra.loc[i_branch,'type'] = type_line
    branch_extra.loc[i_branch,'location_type'] = 'semi-urban'
    branch_extra.loc[i_branch,'installation_year'] = installation_year

# %% Remove reserve column if present
if 'reserve' in branch.columns:
    branch.drop('reserve', axis=1, inplace=True)

# %% Update bus voltage limits

bus['min_Vm'] = Vmin
bus['max_Vm'] = Vmax

# %% Translate bus column names to standard MATPOWER format (but lowercase)

bus_col_translate = {'ID': 'bus_i', 'type': 'bus_type', 'area_num': 'bus_area', 'Va - degr': 'Va',
    'baseKV': 'base_kV', 'max_Vm': 'Vmax', 'min_Vm': 'Vmin'}

bus_cols = bus.columns.to_list()
bus_cols_new = []

for col in bus_cols:
    if col in bus_col_translate.keys():
        bus_cols_new.append( bus_col_translate[col] )
    else:
        bus_cols_new.append(col)

bus.columns = bus_cols_new

# %% Translate branch column names to standard MATPOWER format (but lowercase)

branch_col_translate = {'r': 'br_r', 'x': 'br_x', 'b': 'br_b', 'rateA': 'rate_A',
    'rateB': 'rate_B', 'rateC': 'rate_C', 'ratio': 'tap'}

branch_cols = branch.columns.to_list()
branch_cols_new = []

for col in branch_cols:
    if col in branch_col_translate.keys():
        branch_cols_new.append( branch_col_translate[col] )
    else:
        branch_cols_new.append(col)

branch.columns = branch_cols_new

# %% Create additional bus data (with parameters for ZIP load model)

bus_extra = pd.DataFrame(columns = ['bus_i', 'constant_impedance', 'constant_current', 'constant_power'])
for idx_bus in bus.index:    
    if bus.loc[idx_bus,'Pd'] > 0:
        # As default data, specify a constant power load at each bus with a load point
        bus_extra_newrow = pd.DataFrame(data = {'bus_i': [bus.loc[idx_bus,'bus_i']], 'constant_impedance': [0], 'constant_current': [0], 'constant_power': [1]})
        bus_extra = pd.concat([bus_extra, bus_extra_newrow], axis=0)

# %% Write the modified branch and bus data to .csv files

branch.to_csv(filename_branch_out_fullpath, sep = ';', decimal = decimal_sep_out, index = False)
bus.to_csv(filename_bus_out_fullpath, sep = ';', decimal = decimal_sep_out, index = False)
branch_extra.to_csv(filename_branch_extra_out_fullpath, sep = ';', decimal = decimal_sep_out, index = False)
bus_extra.to_csv(filename_bus_extra_out_fullpath, sep = ';', decimal = decimal_sep_out, index = False)

# %% Do an extra round reading and writing to .csv to include power flow solution in data set (which is a rather awkward solution, I know...)

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10, DiB_version=True)

# Solve power flow equations and update voltage data in the bus matrix
pp.runpp(net, init='results', algorithm='bfsw')
bus['Vm'] = net.res_bus['vm_pu'].to_list()
bus['Va'] = net.res_bus['va_degree'].to_list()

# Write updated bus matrix to file
bus.to_csv(filename_bus_out_fullpath, sep = ';', decimal = decimal_sep_out, index = False)

# Write branch power flow from solution to file
branch_pf_solution = net.res_line[['p_from_mw','q_from_mvar','p_to_mw','q_to_mvar']]
branch_pf_solution.to_csv(filename_branch_pf_solution_new_fullpath, sep = ';', decimal = decimal_sep_out, index = False)


# %% Write the modified grid data to a .xls file
# NB: This requires installing the xlwt package, which will not be supported by pandas in
# the future. The recommendation from pandas is to write to .xlsx files instead.

with pd.ExcelWriter(filename_Excel_out_fullpath) as writer:  
    bus.to_excel(writer, sheet_name='bus', index = False)
    bus_extra.to_excel(writer, sheet_name='bus_extra', index = False)
    branch.to_excel(writer, sheet_name='branch', index = False)
    branch_extra.to_excel(writer, sheet_name='branch_extra', index = False)
    branch_pf_solution.to_excel(writer, sheet_name='branch_pf_solution', index = False)

# %%
