from collections.abc import Iterable

from pymatching import Matching
import numpy as np
import stim

from .stim_tools import from_dem_to_stim, from_stim_to_dem
from .detector_error_model import DEM


def _get_id_from_pymatching_edges(
    edge_array: Iterable[Iterable[int]], dem: DEM
) -> list[int]:
    """Returns the fault ids for the given set of pairs of detectors."""
    list_ids = []

    for edge in edge_array:
        dets = tuple(sorted([e for e in edge if e != -1]))  # -1 for boundary edges
        id_ = dem.det_to_id.get(dets)

        if id_ is None:
            raise ValueError(f"No edge found in DEM that has detectors={dets}")

        list_ids.append(id_)

    return list_ids


def decompose_dem(
    dem: DEM | stim.DetectorErrorModel, ignore_logical_error=False
) -> DEM | stim.DetectorErrorModel:
    """Decomposes a detector error model to edges using Algorithm 3 from
    https://doi.org/10.48550/arXiv.2309.15354.

    Parameters
    ----------
    dem
        Detector error model to decompose.
    ignore_logical_error
        If True, does not raise an error when the found decomposition
        does not have the same logical effect as the undecomposed fault.

    Returns
    -------
    dem
        Decomposed detector error model.

    Notes
    -----
    The algorithm assumes that all the hyperedges in the detector error model
    can be decomposed with existing edges.
    """
    convert_to_stim = False
    if isinstance(dem, stim.DetectorErrorModel):
        convert_to_stim = True
        dem = from_stim_to_dem(dem)

    # Step 1: split the DEM into primitive and non-primitive faults
    # Some hyperedges may already have a decomposition.
    # Some weight-2 edges have a decomposition into weight-1 edges.
    weight_2_edges = []
    hyperedges = []

    for id_, dets in dem.detectors.items():
        if len(dets) == 1:
            dem.set_as_primitive(id_)
            continue

        if not dem.decomposed[id_]:
            if len(dets) == 2:
                weight_2_edges.append(id_)
            else:
                hyperedges.append(id_)

    for edge in weight_2_edges:
        detectors = dem.detectors[edge]
        id1 = dem.prim_det_to_id.get((detectors[0],))
        id2 = dem.prim_det_to_id.get((detectors[1],))

        if (id1 is not None) and (id2 is not None):
            dem.add_decomposition(
                edge, [id1, id2], ignore_logical_error=ignore_logical_error
            )
        else:
            dem.set_as_primitive(edge)

    # Step 2: for every hyperedge run MWPM to obtain the most probable decomposition
    primtive_dem = dem.get_primitive_graph()
    stim_primitive_dem = from_dem_to_stim(primtive_dem)
    MWPM_prim = Matching(stim_primitive_dem)

    if MWPM_prim.num_detectors != Matching(from_dem_to_stim(dem)).num_detectors:
        raise ValueError("Primitive faults do not span all detectors.")

    for hyper in hyperedges:
        det_ids = np.array(dem.detectors[hyper])
        det_vec = np.zeros(MWPM_prim.num_detectors, dtype=bool)
        det_vec[det_ids] = 1

        try:
            edges = MWPM_prim.decode_to_edges_array(det_vec)
        except ValueError as error:
            if "No perfect matching could be found." in error.args[0]:
                raise ValueError(
                    f"No decomposition found for id={hyper} with "
                    f"detectors={det_ids}."
                )
            raise error

        decomposition = _get_id_from_pymatching_edges(edges, dem)
        dem.add_decomposition(
            hyper,
            decomposition,
            ignore_logical_error=ignore_logical_error,
        )

    if convert_to_stim:
        dem = from_dem_to_stim(dem)

    return dem
