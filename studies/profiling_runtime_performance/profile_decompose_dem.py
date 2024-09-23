#!/usr/bin/env python
# coding: utf-8

# # Benchmarking the surface code

# In[1]:

import stim

from hypergraph_decomposition import decompose_dem, from_dem_to_stim, from_stim_to_dem


circuit = stim.Circuit.generated(
    code_task="surface_code:rotated_memory_z",
    distance=11,
    rounds=50,
    after_clifford_depolarization=0.01,
)

dem = from_stim_to_dem(circuit.detector_error_model())
decom_dem = decompose_dem(dem)
decom = from_dem_to_stim(decom_dem)
