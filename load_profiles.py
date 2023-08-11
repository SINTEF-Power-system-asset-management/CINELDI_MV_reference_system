# -*- coding: utf-8 -*-
"""
Created on 2021-12-27

@author: ivespe

Module for handling load profiles, i.e. time series for load demand (typically hourly).
"""

import pandas as pd
import pandapower as pp
import os
from pandas.core.algorithms import isin
from numpy import  sqrt, real, imag, pi
import load_scenarios as ls

class load_profiles(object):
    
    def __init__(self, loaddata_filename:str, normalized = True):
        """
        Initialization of load profiles object. It is assumed that the input data
        are annual load demand time series with hourly resolution (kWh/h) for a set
        of load points, with each column representing a load point.
        
        Inputs:
            loaddata_filename: 
                Full path of load data file (either .xlsx or .csv)

            normalized:
                True if load profile data are already normalized and unitless and meant be used to scale 
                an absolute load value (in kWh/h); False is load data are in absolute values (units kWh/h)
        """

        # Load the load data
        filename, ext = os.path.splitext(loaddata_filename)
        if ext == '.xlsx':
            loaddata = pd.read_excel(loaddata_filename, index_col=0, parse_dates=False)
        elif ext == '.csv':
            loaddata = pd.read_csv(loaddata_filename, sep = ';', index_col=0, parse_dates=False)
        else:
            print('Error: Only .csv and .xlsx load data files supported')
            raise

        # Fix time stamp index of the DataFrame (not really needed, but nice to have for later processing)
        timestamp_list = [i.split(" ") for i in loaddata.index]
        loaddata.index = pd.to_datetime([d + " " + "%.2d" % (int(t) - 1) for d, t in timestamp_list], dayfirst=True)
       
        # Convert column names to integers in case they are strings 
        col_int = [int(i) for i in loaddata.columns.to_list()]
        loaddata.columns = pd.Index(data = col_int)

        # Annual peak load for each bus
        load_max = loaddata.max()
        
        if normalized:
            # The load data are already normalized (and unitless) and can be used to scale a scalar load value (in kW)
            loaddata_rel = loaddata
        else:
            # Relative load profiles, for each bus normalized to annual peak load for that bus
            loaddata_rel = loaddata.divide(load_max)

        # Store variables to object
        self.loaddata_filename = loaddata_filename
        self.loaddata = loaddata
        self.loaddata_rel = loaddata_rel
        self.load_max = load_max


    def get_profile_days(self,days:int):
        """
        Get (relative) load profiles for a given set of days
        
        Inputs:
            days: List of integers for the index of the days of the year to
                to extract load profiles for (1-indexed)
        
        Outputs:
            profile_days: DataFrame with the slices of the relative load profile 
                DataFrame corresponding to the selected days; indices are time steps
                and columns are load IDs
        """

        # Build DataFrame with the time steps corresponding to the selected days
        profile_days = pd.DataFrame(columns = self.loaddata_rel.columns)
        for day in days:
            profile_day = self.loaddata_rel.iloc[(day-1)*24:day*24,:]
            profile_days = pd.concat([profile_days, profile_day])

        # Remove timestamp from index and let index be 0-indexed integers 
        profile_days.reset_index(inplace=True,drop=True)

        return profile_days


    def map_rel_load_profiles(self, filename_load_mapping, repr_days=[29*2+1] ):
        """ 
        Return relative load profiles mapped to existing and new load points in the network

            Inputs:
                filename_load: Full path to load demand data file 
                filename_scenario: Full path to file name defining load-development scenario
                filename_load_mapping: Full path to file defining how load profiles are mapped onto buses of the grid model
                repr_days: List with indices of the days of the year to extract load profiles for (1-indexed);
                    (optional; default: 28 February)

            Outputs:
                mapped_load_profiles: DataFrame with relative load profile (unitless) for 
                    representative days; indices are time steps in days and columns are bus IDs
        """

        # Read load profiles (for representative days)
        profile_repr_days = self.get_profile_days(repr_days)    

        # Read mapping between load IDs in the load data and bus IDs in the network    
        mapping_load_to_bus = pd.read_csv(filename_load_mapping, sep = ';')
        load_IDs = mapping_load_to_bus['time_series_ID'].to_list()
        bus_IDs = mapping_load_to_bus['bus_i'].to_list()

        # Mapped relative load profiles for existing loads in the network
        mapped_load_profiles = profile_repr_days.loc[:,load_IDs]

        # Identifying the profiles with bus in the network rather than load ID in the load data set
        mapped_load_profiles.columns = bus_IDs

        return mapped_load_profiles


    def map_cs_load_profiles(self,mapped_load_profiles,filename_scenario,filename_load_profiles_cs=None,n_days=1):
        """ Add relative load profiles for charging stations to existing mapping of profiles to grid model

            Inputs:   
                mapped_load_profiles: DataFrame with relative load profile (unitless) for 
                    representative days; indices are time steps in days and columns are bus IDs
                filename_scenario: Full path to file name defining load-development scenario
                filename_load_profiles_cs: Path of file name for load profiles for charging stations
                    (Requires a .csv file with exactly 24 hours for each profile)
                n_days: Number of days in the load profile to return 
                    (duplicating the one profile in the input file)

            Outputs:
                mapped_load_profiles: DataFrame with relative load profile (unitless) for 
                    representative days; indices are time steps in days and columns are bus IDs
        """
 
        # Check if charging stations are included in the scenario
        bus_IDs_new_cs_loads, labels_cs_profiles = self.get_bus_IDs_new_cs_loads(filename_scenario)
        if (len(bus_IDs_new_cs_loads) > 0)  & (filename_load_profiles_cs is not None):
            # Read charging station load profile from file
            profile_cs = self.get_cs_load_profiles(filename_load_profiles_cs,labels=labels_cs_profiles,n_days=n_days)
            
            # Add bus numbers for charging stations to mapping
            bus_IDs = mapped_load_profiles.columns.to_list()            
            bus_IDs = bus_IDs + bus_IDs_new_cs_loads
            
            # Extend the mapping with new load points for charging stations
            mapped_load_profiles = pd.concat([mapped_load_profiles, profile_cs], axis = 1)
            mapped_load_profiles.columns = bus_IDs

        return mapped_load_profiles
    

    def get_cs_load_profiles(self,filename_full_cs_load,labels=None,n_days=1):
        """ Return relative load profiles for charging stations

            Inputs:    
                filename_load_profiles_cs: Full path of file name for load profiles for charging stations
                    (Requires a .csv file with exactly 24 hours for each profile)
                labels: List of column headings (labels of the profiles) to return
                n_days: Number of days in the load profile to return 
                    (duplicating the one profile in the input file)

            Outputs:
                profile_cs: Relative load profiles (unitless) for a specified charging stations
        """

        # Read load profiles from file 
        profile_cs_in = pd.read_csv(filename_full_cs_load, sep=';')    
        if profile_cs_in.shape[0] != 24:
            print('Error: Relative load profile inputs for charging stations need to include a full day (24 hours)')
            exit()

        # We let the hours be zero-indexed
        profile_cs_in.drop('hour',axis=1, inplace=True)

        # Duplicate profiles to cover n_days full days
        profile_cs = profile_cs_in.copy()
        for day in range(n_days-1):
            profile_cs = profile_cs.append(profile_cs_in,ignore_index = True)

        # Extract only specified set of load profiles
        if labels is not None:
            profile_cs = profile_cs[labels]

        return profile_cs


    def get_bus_IDs_new_cs_loads(self,filename_fullpath_scenario):
        """ Return bus numbers (IDs) and load profile labels of buses with new 
            charging station loads in a load scenario
            
            Inputs: 
                filename_fullpath_scenario: Full path of filename scenario input filename
                    (see load_scenarios.py for format details)            

            Outputs:
                bus_IDs_new_cs_loads: List with bus numbers (integers) of new 
                    charging station loads
                labels_cs_profiles: List of load profile labels for new 
                    charging station loads (strings)
        """

        # Read load scenario with new loads (assumed to be at buses which currently have no existing load points)
        file_path_split = os.path.split(filename_fullpath_scenario)
        scen_folder = file_path_split[0]
        scen_filename = file_path_split[1]
        scen = ls.read_scenario_from_csv(scen_folder,filename_point_load = scen_filename)
        scen_point_loads = scen['point_loads']
        
        if 'label' not in scen_point_loads.columns:
            print('Can only include charging station loads if load label is specified in scenario')
            return [], ''

        else:    
            # Only consider non-LEC loads (if other types of new loads are included in scenario)
            I_CS = (scen_point_loads['label'] != 'LEC')
            scen_cs_loads = scen_point_loads.loc[I_CS]

            # Bus numbers and load profile labels for new charging station loads
            bus_IDs_new_cs_loads = list(scen_cs_loads['bus_i'].unique())
            labels_cs_profiles = list(scen_cs_loads['label'])
        
            return bus_IDs_new_cs_loads, labels_cs_profiles