import pymatching
import numpy as np

from .stim_tools import from_dem_to_stim
from .detector_error_model import DEM, xor, multiple_xor, g

# # Algorithm
#
# Assuming all hyperedges can be decomposed using existing edges in the DEM,
# then one needs to implement the Algorithm 3 from
# https://doi.org/10.48550/arXiv.2309.15354


def from_pymatching_edges_to_dem_id(edge_array, dem):
    list_ids = []

    for edge in edge_array:
        dets = [e for e in edge if e != -1]  # -1 for boundary edge
        id_ = dem._find_same_fault_id(dets)
        if id_ is not None:
            list_ids.append(id_)
        else:
            raise ValueError(f"No edge found in DEM that has detectors={dets}")

    return list_ids


def decompose_dem(dem: DEM, verbose=True) -> DEM:
    # Step 1: split the DEM into primitive and non-primitive faults
    weight_2_edges = []
    hyperedges = []

    for id_ in dem.ids:
        detectors = dem.detectors[id_]
        if len(detectors) == 1:
            dem.add_primitive(id_)

    # some hyperedges may already have a decomposition
    for id_ in dem.get_undecomposed_faults():
        detectors = dem.detectors[id_]
        if len(detectors) == 2:
            weight_2_edges.append(id_)
        else:
            hyperedges.append(id_)

    for edge in weight_2_edges:
        detectors = dem.detectors[edge]
        logicals = dem.logicals[edge]
        if ((detectors[0],) in dem.prim_det_to_id) and (
            (detectors[1],) in dem.prim_det_to_id
        ):
            id1 = dem.prim_det_to_id[(detectors[0],)]
            id2 = dem.prim_det_to_id[(detectors[1],)]
            if xor(dem.logicals[id1], dem.logicals[id2]) == logicals:
                dem.add_decomposition(edge, [id1, id2])
            else:
                if verbose:
                    print(
                        "Warning: the logical effect of an edge is different than its weight-1 decomposition"
                    )
                dem.add_primitive(edge)
        else:
            dem.add_primitive(edge)

    # Step 2: for every hyperedge run MWPM to obtain the most probable decomposition
    primtive_dem = dem.get_primitive_graph()
    stim_primitive_dem = from_dem_to_stim(primtive_dem)
    MWPM_prim = pymatching.Matching(stim_primitive_dem)

    for hyper in hyperedges:
        det_ids = dem.detectors[hyper]
        det_vec = np.zeros(MWPM_prim.num_detectors, dtype=bool)
        det_vec[det_ids] = 1
        edges = MWPM_prim.decode_to_edges_array(det_vec)
        decomposition = from_pymatching_edges_to_dem_id(edges, dem)
        dem.add_decomposition(hyper, decomposition)

    return dem.get_decomposed_graph()
