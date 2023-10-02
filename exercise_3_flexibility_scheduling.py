# -*- coding: utf-8 -*-
"""
Created on Fri Mar 31 15:30:27 2023
@author: merkebud
"""
#REFERENCES
#https://pyomo.readthedocs.io/en/stable/contributed_packages/mindtpy.html
#https://coin-or.github.io/Ipopt/index.html

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pyomo.opt import SolverFactory
from pyomo.core import Var
import pyomo.environ as en
import time


#Read battery specification 
parametersinput = pd.read_csv('./battery_data.csv', index_col=0)
parameters = parametersinput.loc[1]

#Battery Specification
capacity=parameters['Battery_Capacity']
charging_power_limit=parameters["Battery_Power"]
discharging_power_limit=parameters["Battery_Power"]
charging_efficiency=parameters["Battery_Charge_Efficiency"]
discharging_efficiency=parameters["Battery_Discharge_Efficiency"]

# Read load and PV profile data
testData = pd.read_csv('./profile_input.csv')

# Convert the various timeseries/profiles to numpy arrays
load1 = testData['Base_Load'].values
PV1 = testData['PV'].values
sellPrice = testData['Feed_Price'].values
buyPrice = testData['Load_Price'].values
