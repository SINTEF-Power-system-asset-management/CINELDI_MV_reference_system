# -*- coding: utf-8 -*-
"""
Created on 2022-09-02

@author: ivespe

Module for implementing grid investments and evaluating their costs.
"""

import pandas as pd

class grid_investment(object):
    
    def __init__(self, cable_data_filename_fullpath:str, reinf_strategy_filename_fullpath:str):
        """
        Initialization of object for managing grid investment costs.
        
        Inputs:
            cable_data_filename_fullpath: 
                Full path of data file (.csv) for grid investment costs
            reinf_strategy_filename_fullpath:
                Full path of data file (.csv) for grid reinforcement strategy
            
        """

        # Read technical and economic data for cables
        cable_data = pd.read_csv(cable_data_filename_fullpath,sep=';')

        # Add entry for fictitious line (TODO: Should not be hard-coding this?)
        cable_data_fictitious = pd.DataFrame(index = ['fictitious line'], data = {'type': 'fictitious line', 'R_ohm_per_km': 0.001, 'X_ohm_per_km': 0.001, 'Cd_nF_per_km': 0, 'Imax_A': 999, 'cost_NOK_per_km_rural': 1e9, 'cost_NOK_per_km_semi-urban': 1e9, 'cost_NOK_per_km_urban': 1e9})
        cable_data = pd.concat([cable_data, cable_data_fictitious], axis = 0)

        cable_data.set_index(cable_data['type'],drop=True,inplace=True)
        self.cable_data = cable_data

        # Series with the main type ('underground_cable', 'overhead_line', etc. for 
        # all components, indexed by the component name, which is assumed to be unique)
        #  NB: For now assuming that all components are underground cables
        cable_types = cable_data['type']
        main_types = pd.Series(dtype = str, index = cable_types.to_list())
        main_types[:] = 'underground_cable'
        self.main_types = main_types

        reinf_strategy = pd.read_csv(reinf_strategy_filename_fullpath,sep=';')
        self.reinf_strategy = reinf_strategy


    def calc_inv_cost_branch(self,net,branch_id,type_new,replace=True):
        """ Calculate investment costs (or rather installation costs) for a new branch

            Inputs:
                net: pandapower network object
                branch_id: Index of branch in the line pandapower DataFrame
                type_new: Name of branch type

            Outputs:
                inv_cost: Investment costs for new branch

            TODO: Implement support for input parameter replace
            TODO: Implement support for transformers; if there are transformers in the input data on
                MATPOWER format then the pandapower line DataFrame will have different indexes than the branch input matrix
        """   

        length_branch = net.branch_extra.loc[branch_id,'length_km']    
        location_type = net.branch_extra.loc[branch_id,'location_type']

        # Whether the new branch type is an underground cable or overhead line
        # TODO: Add support for overhead lines and other component types
        main_type = self.main_types.loc[type_new] 

        if main_type == 'underground_cable':
            # Find the right installation cost for the location of the branch 
            # (since installation costs depend on the cost of excavation/trenches)
            if location_type == 'rural':
                cost_per_km = self.cable_data.loc[type_new,'cost_NOK_per_km_rural']
            elif location_type == 'semi-urban':
                cost_per_km = self.cable_data.loc[type_new,'cost_NOK_per_km_semi-urban']
            elif location_type == 'urban':
                cost_per_km = self.cable_data.loc[type_new,'cost_NOK_per_km_urban']
            else:
                print('Error: Location type not supported')
                exit

        else:
            print('Error: Only underground cables are supported at the moment')
            exit

        # Remove spaces and make into a number 
        # (TODO: Should fix the data file in the next update so there are no spaces in what is supposed to be numbers...)
        if isinstance(cost_per_km,str):
            cost_per_km = float(cost_per_km.replace(" ", ""))

        # Calculate costs for installing a given length of the branch type
        inv_cost = length_branch * cost_per_km        
        return inv_cost


    def select_reinforcement(self,branch_id,net):
        """ Select branch type for grid reinforcement based on reinforcement strategy

            Inputs:
                branch_id: Branch index for branch to be reinforced, referring to the 'line'
                    DataFrame in the pandapower network
                net: pandapower network dictionary
                
            Outputs:
                type_new: Component type of reinforced branch

            TODO: Could also consider different component types, or whether or not to suggest
                underground cables when reinforcing overhead lines
        """   

        Imax_A_existing = round(net.line.loc[branch_id,'max_i_ka'] * 1000)
        existing_Imax_A_upper = self.reinf_strategy['existing_Imax_A_upper']
        
        if Imax_A_existing == 999:
                # Ugly hack to avoid suggesting any upgrades to the fictitious lines <- TODO: Clean up
                type_new = 'fictitious line'
        else:
        # Simple reinforcement strategy where one increases the capacity to the next level (rating) 
        # for a pre-defined set of rating levels
            i_reinf_strategy = existing_Imax_A_upper.index[existing_Imax_A_upper >= Imax_A_existing][0]
            type_new = self.reinf_strategy.loc[i_reinf_strategy,'type_new']
        
        return type_new



    def replace_branch(net,branch_ids,branch_types):
        """ Replace a set of branches with new (upgrades/reinforced branches)

            Inputs:
                net: pandapower network dictionary
                branch_ids: List of branch IDs, referring to the line DataFrame in the pandapower network
                branch_types: 

            Outputs:
                net: pandapower network DataFrame after grid investment measures are implemented
                install_costs: List with installation costs of new branches
        """   

        install_costs = 0 * len(branch_ids)
        #TODO

        return net, install_costs
