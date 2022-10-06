# -*- coding: utf-8 -*-
"""
Created on 2021-11-02

@author: ivespe

Module for handling scenarios for the long-term development of load demand in distribution system.
"""

import pandas as pd
import pandapower as pp
import os
import math
from pandas.core.algorithms import isin


def apply_scenario_to_net(net,scenario_data,year, load_scale=1.0, power_factor=0.95):
    """ Modify network  to be consistent with long-term load scenario for some future year

        Inputs:
            net: pandapower network DataFrame
            scenario_data: Dictionary with entries 'point_load' for new and increased point loads
                and 'base_load' for general increase (or decrease) in the 'base load' at existing 
                load points. The value for key 'point_load' is a DataFrame with one row (scenario entry) 
                for each addition of load demand at a given bus at a given year. Column 'year' is year
                relative to the present year (0), column 'bus' refers to the bus number of the network, 
                column 'load added (MW)' is the real power in MW
            year: which year in the scenario that the operating state should be consistent with. 
                (Linear interpolation is applied if the load demand is not specified for this year in 
                the scenario)
            load_scale: Scaling factor to apply to the load demand value in the scenario data 
                (optional; default: 1.0, i.e., no scaling)
            power_factor: Power factor (lagging) to use for all new loads if no power factor is specified 
                for individual loads in the scenario input data (optional; default: 0.95)

        Return:
            net: pandapower network DataFrame modified with new load points (if necessary)

            
        NB: Only scenarios for point loads are currently implemented. 
    """ 
    
    years = scenario_data['point_loads']['year_rel']
    buses = scenario_data['point_loads']['bus_i']
    load_add = scenario_data['point_loads']['load_added_MW']

    if 'power_factor' in scenario_data['point_loads'].columns:
        # Use provided power factors for each new load
        power_factor_vec = scenario_data['point_loads']['power_factor']
    else:
        # If power factors are not provided for new loads, use either default value or 
        # a single custom value provided as input argument
        power_factor_vec = [power_factor] * len(load_add)

    for it in years.index:
        if years[it] <= year:
            # Loop through all years up to the year we want to consider
            bus_ID = buses[it]
            load_name = int(bus_ID)
            if any(net.load['bus'] == bus_ID) == False:
                # Add load to bus if none exist; set reactive power for load using a fixed power factor
                Pd = load_add[it]*load_scale
                Qd = Pd * math.tan(math.acos(power_factor_vec[it]))
                pp.create_load(net,bus=bus_ID,name=load_name,p_mw=Pd,q_mvar=Qd)
            
                # Reindex so that DataFrame row index is bus name for all loads
                net.load.set_index('name',drop=False,inplace=True)
    
            else:
                # Increase power consumption if there already is a load at the bus
                net.load.loc[load_name,'p_mw'] += load_add[it]

    return net


def read_scenario_from_csv(folder, filename_point_load):
    """ Generate scenarios for long-term load development from .csv input file

        Inputs:
            folder: Folder with files specifying scenarios
            filename_point_load: File name (in folder) for data file specifying new point loads
                that are added 

        Return:
            scenario_data: Dictionary with entries 'point_load' for new and increased point loads
                and 'base_load' for general increase (or decrease) in the 'base load' at existing 
                load points.
                The value for key 'point_load' is a DataFrame with one row (scenario entry) for each 
                addition of load demand at a given bus at a given year. Column 'year' is year relative to 
                the present year (0), column 'bus' refers to the bus number of the network, 
                column 'load added (MW)' is the real power in MW                            
                (NB: Functionality for 'base load' is not reimplemented)

    """ 
   # File names in specified folder
    filename_point_loads_fullpath = os.path.join(folder, filename_point_load)

    # Read files from .csv files
    scenario_base_load = None
    scenario_point_loads = pd.read_csv(filename_point_loads_fullpath,sep=';')

    # Put together scenario data output
    scenario_data = {'base_load': scenario_base_load, 'point_loads': scenario_point_loads}

    return scenario_data


def interp_for_scenario(df,years_interp):
    """ Interpolate data evaluated for specific years in a scenario. The only type of interpolation
        that is currently supported is to let values for missing years be the previous explicitly
        evaluated year.

        Inputs:
            df: pandas DataFrame of Series with index being the years of the scenario that 
                has been explicitly evaluated
            years_interp: Years that the values are to be interpolated for.
            

        Output:
            df_interp: DataFrame with index equals years_interp and interpolated values for all 
            these years.
    """ 

    # Index needs to be years    
    years = df.index

    # Hack to be able to support Series (that don't have columns) as well as DataFrames
    if len(df.shape) == 1:
        df_interp = pd.DataFrame(index = years_interp, columns = ['value'])
    else:
        df_interp = pd.DataFrame(index = years_interp, columns = df.columns)
    
    if years_interp[0] != years[0]:
        print('First year of new list of year for interpolation needs to equal first year in the original list of years')        
        raise

    # Loop over all years that values are to be returned for
    for year in years_interp:
        I = list(years == year)
        if any(I):
            values = list(df.loc[I].values[0])
            df_interp.loc[year] = values
        else:
            df_interp.loc[year] = values_prev

        # Store values for the previous years that are explicitly evaluated
        values_prev = values

    return df_interp