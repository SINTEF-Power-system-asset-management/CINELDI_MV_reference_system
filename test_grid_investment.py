# -*- coding: utf-8 -*-
"""
Created on 2022-09-03

@author: ivespe

Script for testing code for grid investments
"""

# %% Dependencies

import os
import pandas as pd
from pandapower_read_csv import read_net_from_csv
import grid_dev_plan as gdp

# %% Set up file names and parameters

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'

# Location of input data for this example that is not part of the CINELDI MW reference system
# (Now it is assumed that example data is in the same folder)
example_data_folder = os.path.abspath('.')

# Set file names and paths
filename_std_cable_types = 'standard_underground_cable_types.csv'
filename_reinf_strategy = 'grid_reinforcement_strategy.csv'
cable_data_filename_fullpath = os.path.join(path_data_set,filename_std_cable_types)
reinf_strategy_filename_fullpath = os.path.join(example_data_folder,filename_reinf_strategy)

# %% Read CINELDI reference network to pandapower network object
net = read_net_from_csv(path_data_set, baseMVA=10, DiB_version = True)

# %% Initialize object for handling grid investments
grid_inv_data = gdp.grid_investment(cable_data_filename_fullpath,reinf_strategy_filename_fullpath)

# %% Calculate costs of replacing overhead line from bus 5 to bus 72 by underground cable

branch_ids = [branch_id for branch_id in range(4,23)]
inv_costs = pd.Series(index=branch_ids)

for branch_id in branch_ids:
    type_new = grid_inv_data.select_reinforcement(branch_id,net)
    inv_costs[branch_id] = grid_inv_data.calc_inv_cost_branch(net,branch_id,type_new)

inv_cost_sum = inv_costs.sum()
