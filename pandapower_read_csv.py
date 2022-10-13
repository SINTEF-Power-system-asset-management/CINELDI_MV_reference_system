"""
Created on 2021-10-31

@author: ivespe

Module for loading and setting up pandapower network object for the CINELDI MV 
reference grid based on input .csv files on the MATPOWER format.
"""

import pandas as pd
import os
import pandapower as pp
import math


def read_net_from_csv(folder, baseMVA=10, DiB_version = True):
    """ Read network data from .csv file and convert to pandapower

        Inputs:
            folder: path of folder with grid data files
            baseMVA: Base apparent power value to use in the per-unit conversion 
                (optional; default: 10 MVA)
            DiB_version: True if assuming files and file names as for data set published 
                in connection with Data in Brief (DiB) manuscript; False if assuming 
                previous version (until around August 2022)

        Outputs:
            net: pandapower net DataFrame for network            
    """

    # Hard coding file names for CINELDI reference grid data
    if DiB_version:
        filename_bus = 'CINELDI_MV_reference_grid_base_bus.csv'
        filename_branch = 'CINELDI_MV_reference_grid_base_branch.csv'
        filename_branch_extra = 'CINELDI_MV_reference_grid_base_branch_extra.csv'
        filename_bus_extra = 'CINELDI_MV_reference_grid_base_bus_extra.csv'        
    else:
        filename_bus = 'Cineldi124Bus_Busdata.csv'
        filename_branch = 'Cineldi124Bus_Branch.csv'
        filename_branch_extra = 'Cineldi124Bus_Branch_extra.csv'

    # Read files from .csv files
    filename_bus_fullpath = os.path.join(folder, filename_bus)
    filename_branch_fullpath = os.path.join(folder, filename_branch)    
    bus = pd.read_csv(filename_bus_fullpath,sep=';')
    branch = pd.read_csv(filename_branch_fullpath,sep=';')

    # Only try to read extra branch data if input file exists
    filename_branch_extra_fullpath = os.path.join(folder, filename_branch_extra)
    branch_extra_exists = os.path.isfile(filename_branch_extra_fullpath)
    if branch_extra_exists:
        branch_extra = pd.read_csv(filename_branch_extra_fullpath,sep=';')        

    # Assuming the grid to be operated at frequency 50 Hz
    f_hz = 50.0

    # Initialize pandapower network
    net = pp.create_empty_network(name='CINELDI_reference_grid', f_hz=f_hz, sn_mva=baseMVA, add_stdtypes=True)

    # Initialize pandapower power flow results DataFrame
    res_bus = pd.DataFrame(columns = ['vm_pu','va_degree','p_mw','q_mvar'])

    if 'baseKV' in bus.columns:
        s_base_kV = bus['baseKV']
    else:
        s_base_kV = bus['base_kV']

    # Read bus and load data
    for i_bus in bus.index:
        
        if 'ID' in bus.columns:
            bus_ID = bus.loc[i_bus,'ID']
        else:
            bus_ID = bus.loc[i_bus,'bus_i']
        
        if not pd.isna(bus_ID):
            # Read data from .csv file (but there are some NaN rows that should be omitted)

            bus_name = int(bus_ID)
            vn_kv = s_base_kV[i_bus]
            bus_type = 'b'
            zone = bus.loc[i_bus,'zone']
            in_service = True
            if 'Va - degr' in bus.columns:
                Va_degrees  = bus.loc[i_bus,'Va - degr']
            else:
                Va_degrees  = bus.loc[i_bus,'Va']
            Vm = bus.loc[i_bus,'Vm']
            if 'max_Vm' in bus.columns:
                max_vm_pu = bus.loc[i_bus,'max_Vm']
            else:
                max_vm_pu = bus.loc[i_bus,'Vmax']
            if 'max_Vm' in bus.columns:
                min_vm_pu = bus.loc[i_bus,'min_Vm']            
            else:
                min_vm_pu = bus.loc[i_bus,'Vmin']            
            Pd = bus.loc[i_bus,'Pd']
            Qd = bus.loc[i_bus,'Qd']

            # Fix problem with decimal operators ',' used in the .csv file
            if type(vn_kv) == str:
                vn_kv = float(vn_kv.replace(',','.'))
            if type(zone) == str:
                zone = float(zone.replace(',','.'))
            if type(max_vm_pu) == str:
                max_vm_pu = float(max_vm_pu.replace(',','.'))
            if type(min_vm_pu) == str:
                min_vm_pu = float(min_vm_pu.replace(',','.'))
            if type(Va_degrees) == str:
                Va_degrees = float(Va_degrees.replace(',','.'))
            if type(Vm) == str:
                Vm = float(Vm.replace(',','.'))
            if type(Pd) == str:
                Pd = float(Pd.replace(',','.'))                
            if type(Qd) == str:
                Qd = float(Qd.replace(',','.'))     

            # Adding bus  to network
            pp.create_bus(net,index=bus_ID,name=bus_name,vn_kv=vn_kv,type=bus_type, zone=zone, in_service=in_service, max_vm_pu=max_vm_pu, min_vm_pu=min_vm_pu)

            # Adding corresponding entry in results DataFrame
            res_row = pd.DataFrame({'vm_pu': [Vm], 'va_degree': [Va_degrees], 'p_mw': [Pd], 'q_mvar': [Qd]}, index=[bus_ID])
            res_bus = pd.concat([res_bus, res_row])

            if Pd != 0 and Qd != 0:
                # Adding load to network for this bus
                # (NB: Now we use the bus number as name for the bus; 
                # this assumes there will only be one load per bus, but that may change...)
                pp.create_load(net,bus=bus_ID,name=bus_name,p_mw=Pd,q_mvar=Qd)

    # Set the row indices for the load DataFrame to be the load names
    net.load.set_index('name',drop=False,inplace=True)

    # Add bus results DataFrame to network
    net.res_bus = res_bus

    # Read line data (and we assume there are no transformers)
    for i_branch in branch.index:
        f_bus = branch.loc[i_branch,'f_bus']
        t_bus = branch.loc[i_branch,'t_bus']
        if 'r' in branch.columns:
            r = branch.loc[i_branch,'r']
        else:
            r = branch.loc[i_branch,'br_r']
        if 'x' in branch.columns:
            x = branch.loc[i_branch,'x']
        else:
            x = branch.loc[i_branch,'br_x']
        if 'b' in branch.columns:
            b = branch.loc[i_branch,'b']
        else:
            b = branch.loc[i_branch,'br_b']        
        if 'rateA' in branch.columns:
            rateA = branch.loc[i_branch,'rateA']
        else:
            rateA = branch.loc[i_branch,'rate_A']
        if 'rateB' in branch.columns:
            rateB = branch.loc[i_branch,'rateB']
        else:
            rateB = branch.loc[i_branch,'rate_B']
        if 'rateC' in branch.columns:
            rateC = branch.loc[i_branch,'rateC']
        else:
            rateC = branch.loc[i_branch,'rate_C']
        shift = branch.loc[i_branch,'shift']
        br_status = branch.loc[i_branch,'br_status']

        # Fix problem with decimal operators ',' used in the .csv file
        if type(r) == str:
            r = float(r.replace(',','.'))
        if type(x) == str:
            x = float(x.replace(',','.'))
        if type(b) == str:
            b = float(b.replace(',','.'))
        if type(rateA) == str:
            rateA = float(rateA.replace(',','.'))                
        if type(rateB) == str:
            rateB = float(rateB.replace(',','.'))   
        if type(rateC) == str:
            rateC = float(rateC.replace(',','.'))
        if type(shift) == str:
            shift = float(shift.replace(',','.'))   
        if type(br_status) == str:
            br_status = float(br_status.replace(',','.'))
        
        # Converting line rating to units kA from units MVA
        base_kV = s_base_kV[f_bus]
        max_i_ka = rateA / base_kV  / math.sqrt(3)

        # Base impedance value (ohm)
        Zni = base_kV**2/baseMVA  

        # pandapower assumes impedance to be given in ohm per km and in addition specifies line length in km;
        # we give impedances in ohm and set the length to 1
        length_km = 1

        # Converting from p.u. to ohm
        r_ohm = r * Zni
        x_ohm = x * Zni

        # Converting charging susceptance from p.u. to ohm
        omega = math.pi * f_hz  # 1/s
        c_nf_per_km = b/Zni/omega*1e9/2

        # Adding line to network
        pp.create_line_from_parameters(net, from_bus=f_bus, to_bus=t_bus, length_km=length_km, r_ohm_per_km = r_ohm, x_ohm_per_km = x_ohm, c_nf_per_km = c_nf_per_km, max_i_ka = max_i_ka, in_service=br_status)

    # Specify main feeder (MF) and point of common coupling to the external (HV) power grid
    bus_MF = 1
    pp.create_ext_grid(net, bus_MF)
  
    if branch_extra_exists:
        net.branch_extra = branch_extra

    return net
