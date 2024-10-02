# hypergraph-decomposition

![example workflow](https://github.com/MarcSerraPeralta/hypergraph-decomposition/actions/workflows/actions.yaml/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Decomposition of hypergraphs for QEC using Algorithm 3 from https://arxiv.org/pdf/2309.15354.pdf


## Installation

Currently, this package can only be installed from source code. 
For Unix-like systems, one can install it using the following commands:
```
git clone git@github.com:MarcSerraPeralta/hypergraph-decomposition.git
pip install hypergraph_decomposition/
```


## Usage

### from `stim.DetectorErrorModel`

Any Detector Error Model (DEM) from stim can be decomposed by

```
from hyper_decom import decompose_dem

dem = stim.DetectorErrorModel(...)

decom_dem = decompose_dem(dem)
```

### Using list of (hyper)edges and their probabilities

First, one needs to build the DEM using `hyper_decom.DEM` and then decompose it.

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

graph_dem = decom_dem.get_decomposed_dem()
```

Note that `decom_dem` contains the same faults as `dem` but including the decomposition information.
However, `graph_dem` only contains faults triggering at most two edges, with updated probabilities taking into account the hyperedges.
