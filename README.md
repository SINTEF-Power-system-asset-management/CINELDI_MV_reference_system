# CINELDI_MV_reference_system
Code for processing and analysing a reference data set for a Norwegian medium voltage power distribution system (the CINELDI MV reference system). The reference data set is available with doi:[10.5281/zenodo.7703070](https://doi.org/10.5281/zenodo.7703070). The data set is described in the following data article: I. B. Sperstad, O. B. Fosso, S. H. Jakobsen, A. O. Eggen, J. H. Evenstuen, and G. Kjølle, ‘Reference data set for a Norwegian medium voltage power distribution system’, Data in Brief, 109025, Mar. 2023, doi:[10.1016/j.dib.2023.109025](https://doi.org/10.1016/j.dib.2023.109025).

## Usage
To install the code package, first download it to a local folder. The associated data set (doi:10.5281/zenodo.7703070) must also be downloaded to a local folder, and before the code is used, the path to this data folder must be specified in the code scripts.

To handle dependencies, [uv](https://docs.astral.sh/uv/) can be used for package management.

If you have not already installed uv, you can do so by running:

```bash
pip install uv
```

Alternatively, uv can also be installed by running:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Dependencies can then be installed by going to the local code folder and running:

```bash
uv sync
```

To run the code directly from the terminal, the the virtual environment that has been created can be activated by running:
```bash
.\.venv\Scripts\activate
```

Make sure the Python kernel for the virtual environment (`cineldi-mv-reference-system`) is selected before running the Jupyter Notebook. (If you are using VC Code, you may have to restart the app first.)


## Overview of code: 
The following files are found in the main branch of the repository. In addition, the extended_reference_grids branch hosts experimental "extensions" (variants) of the reference grid.

### calc_share_customer_type.py
Code for calculating the share of load per customer type for each load time series in the load data set for the CINELDI MV reference system.

### create_load_mapping.py
Script for creating mapping between the 104 load time series (load IDs) in the load data set and bus IDs of the 124-bus CINELDI MV reference grid.

### create_grid_with_load_snapshot.py
Script for creating a version of the grid data set for a certain operating state, obtained for a "snapshot" for a given day and hour of the year from the load demand time series

### load_profiles.py
Module for handling load profiles, i.e. time series for load demand (typically hourly).

### load_scenarios.py
Module for handling scenarios for the long-term development of load demand in distribution system.

### pandapower_read_csv.py
Module for loading and setting up pandapower network object for the CINELDI reference grid based on input .csv files on the MATPOWER format.

### test_extract_load_time_series.py
Script for extracting load time series in units MWh/h for existing load points in the CINELDI reference grid

### prepare_reldata.py
Script for preparing data for reliability analysis (load point data and component reliability data) 
for the CINELDI MV reference system.

### process_grid_data.py
Script for processing the CINELDI MV reference grid by adding charging susceptance based on standard line type information from Planleggingsbok for kraftnett and estimating line lengths. Also updating format of files to standard MATPOWER format.

### test_analysis_CINELDI_MV_system.py
Test script for simple power flow analyses by applying load development scenarios and 
load time series to the CINELDI MV reference system.


## License
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Authors
Contributors: Iver Bakken Sperstad, Julie Helen Evenstuen, Espen Flo Bødal

Copyright (C) 2022-2023 SINTEF Energi AS

## Funding
This work is funded by CINELDI - Centre for intelligent electricity distribution, an 8 year Research Centre under the FME-scheme (Centre for Environment-friendly Energy Research, 257626/E20). The authors gratefully acknowledge the financial support from the Research Council of Norway and the CINELDI partners.
