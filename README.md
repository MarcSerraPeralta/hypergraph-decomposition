# hypergraph-decomposition
Decomposition of hypergraphs for QEC using Algorithm 3 from https://arxiv.org/pdf/2309.15354.pdf

# Usage

## Using stim DEM

The motivation for using this algorithm instead of stim's build in `circuit.detector_error_model(decompose_errors=True)` method is that stim can fail to decompose some hyperedges that have a valid decomposition. 

Any Detector Error Model (DEM) from stim can be decomposed by

```
from hypergraph_decomposition import from_stim_to_dem, decompose_dem, from_dem_to_stim

dem_stim = stim.DetectorErrorModel("...")

dem = from_stim_to_dem(dem_stim)
decom_dem = decompose_dem(dem)

# to get back the decomposed DEM in stim's format
decom_stim = from_dem_to_stim(decom_dem)
```

As stim performs a slightly better job at decomposing the hyperedges (see `benchmarks`), one can use stim's decomposition for the hyperedges it can decompose and Algorithm 3 for the rest of the hyperedges. This is implemented by

```
from hypergraph_decomposition import from_stim_to_dem, decompose_dem, from_dem_to_stim

circuit = stim.Circuit("...")
dem_stim = circuit.detector_error_model(decompose_errors=True, ignore_decomposition_failures=True)

dem = from_stim_to_dem(dem_stim)
decom_dem = decompose_dem(dem)

# to get back the decomposed DEM in stim's format
decom_stim = from_dem_to_stim(decom_dem)
```

# Using list of (hyper)edges and their probabilities

First, one needs to build the DEM:

```
from hypergraph_decomposition import DEM, decompose_dem

# list of hyperedges where the elements are a length-3 list with the following data:
# (1) probabilitiy of the (hyper)edge
# (2) ids of the detectors triggered by the (hyper)edge
# (3) ids of the logical observables flipped by the (hyper)edge
inputs = [[p_1, d_1, l_1], [p_2, d_2, l_2], ...] 

dem = DEM()
for p, d, l in inputs:
	dem.add_fault(p, d, l)

decom_dem = decompose_dem(dem)

# get the probabililities, detectors and logical effects of the decomposed DEM
output = []
for id_ in decom_dem.ids:
	p = decom_dem.probs[id_]
	d = decom_dem.detectors[id_]
	l = decom_dem.logicals[id_]
	output.append([p, d, l])
```

