# # -*- coding: utf-8 -*-

"""
# Created on 2022-07-07

# @author: julie evenstuen

# Code for calculating the share of load per customer type for each load time series in the load data set for the 
# CINELDI MV reference system.
"""

# %% Set-up and parameters
from numpy import unique
import numpy as np
import pandas as pd
from numpy.matlib import matrix,rand,zeros,ones,empty,eye
from io import StringIO
import os


# %% Importing the file from correct path/location

# Location of orignal load data set
path_input             = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/load_data_input/'

#  Path of folder with processed data set
path_output = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system'

filename_in         = 'load_data_set_original'

filename_out        = 'share_load_per_customer_type'        

# %% Read original (restricted) load data set from file
df              = pd.read_excel(path_input+filename_in+'.xlsx')        # read a xlsx file
df.fillna(0,inplace=True)                                           # Remove any NaN values

irow_trafonr            = 0                             # Row with transformer (i.e., distribution substation) numbers (load time series IDs) 
irow_customer_types     = 1                             # Row with load/customer types ("Husholdning, ...")
irow_data_start         = 3                             # Row where load data starts
n_hours                 = df.shape[0]-irow_data_start   # Number of hours of load data

# Retrieve all the categories, and then find the unique ones
trafonrs_all            = df.iloc[irow_trafonr,1:]           # Reading from row with all trafonr 
trafonrs_all.reset_index(inplace=True,drop=True)             # Changing index-name to numbers: 0, 1, 2
trafonrs_unik           = trafonrs_all.unique()              # Finding all unique trafonr

cats_all                = df.iloc[irow_customer_types,1:]    # Position of row with all customer types
cats_unik               = cats_all.unique()                  # Finding all unique customer types

#  Create a zero matrix (table to be filled in)
cats_unik2              = cats_unik.copy()
cats_unik2              = np.insert(cats_unik2,0,'time_series_ID')
finaltable              = zeros((len(trafonrs_unik),1+len(cats_unik)),dtype=float)
finaltable              = pd.DataFrame(finaltable, columns = cats_unik2)            # rows = trafonrs_unik
finaltable.iloc[:,0] = finaltable.iloc[:,0].astype(int)

print(finaltable)

# %% Nested for loop, where we examine for all distribution transformers, and for all categories for each transformer
for i_trafo in range(len(trafonrs_unik)):
    trafonr             = trafonrs_unik[i_trafo]
    icol_trafonrs       = (trafonrs_all == trafonr)                             # col index for relevant trafo
    icol_trafonrs       = [False] + icol_trafonrs.tolist()

    cat_trafo           = df.iloc[irow_customer_types,icol_trafonrs]
    
    data_trafo          = df.iloc[irow_data_start:,icol_trafonrs].to_numpy()   
    data_trafo          = pd.DataFrame(data_trafo, columns = cat_trafo)
    
    # Calculate total annual energy demand for each trafo (distribution substation)
    data_trafo_sum      = data_trafo.sum(0)
    data_trafo_sum_sum = data_trafo_sum.sum()

    if data_trafo_sum_sum > 0:
        # Calculate share of annual energy demand 
        data_trafo_andel    = data_trafo_sum/data_trafo_sum_sum
    else:
        # To avoid division by zero for trafos with zero annual energy demand
        data_trafo_andel = [0] * len(data_trafo_sum)
    
    finaltable.iloc[i_trafo,0] = i_trafo+1
    for i_cat in range(len(cat_trafo)):
        cat             = cat_trafo[i_cat]
        i_cat_tab       = (cats_unik2 == cat)

        finaltable.iloc[i_trafo,i_cat_tab] = data_trafo_andel[i_cat]

# %% Translate customer types from Norwegian to English
cat_translate = {'Husholdning': 'residential', 'Jordbruk': 'agriculture', 'Offentlig virksomhet':'public', 
    'Industri':'industry', 'Handel og tjenester':'commercial', 'Industri med eldrevne prosesser': 'energy-intensive industries'}
cats_Norwegian = finaltable.columns.to_list()
cats_English = []

for cat in cats_Norwegian:
    if cat in cat_translate.keys():
        cats_English.append( cat_translate[cat] )
    else:
        cats_English.append(cat)

finaltable.columns = cats_English

# %% Write to file
filename_output_fullpath = os.path.join(path_output,filename_out+'.csv')
finaltable.to_csv(filename_output_fullpath,index=False,sep=';')

# %%
