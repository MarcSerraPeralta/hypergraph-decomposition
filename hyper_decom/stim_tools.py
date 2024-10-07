import stim

from .detector_error_model import DEM, xor_lists


def get_detectors(dem_instr: stim.DemInstruction) -> tuple[int, ...]:
    if dem_instr.type != "error":
        raise ValueError(f"DemInstruction is not an error, it is {dem_instr.type}.")

    if has_separator(dem_instr):
        return xor_lists(*decomposed_detectors(dem_instr))
    else:
        return tuple(
            i.val for i in dem_instr.targets_copy() if i.is_relative_detector_id()
        )


def get_logicals(dem_instr: stim.DemInstruction) -> tuple[int, ...]:
    if dem_instr.type != "error":
        raise ValueError(f"DemInstruction is not an error, it is {dem_instr.type}.")

    if has_separator(dem_instr):
        return xor_lists(*decomposed_logicals(dem_instr))
    else:
        return tuple(
            i.val for i in dem_instr.targets_copy() if i.is_logical_observable_id()
        )


def has_separator(dem_instr: stim.DemInstruction) -> bool:
    if dem_instr.type != "error":
        raise ValueError(f"DemInstruction is not an error, it is {dem_instr.type}.")

    return bool([i for i in dem_instr.targets_copy() if i.is_separator()])


def decomposed_detectors(dem_instr: stim.DemInstruction) -> list[tuple[int, ...]]:
    if dem_instr.type != "error":
        raise ValueError(f"DemInstruction is not an error, it is {dem_instr.type}.")

    list_dets = []
    current = []
    for e in dem_instr.targets_copy():
        if e.is_separator():
            list_dets.append(current)
            current = []
        if e.is_relative_detector_id():
            current.append(e.val)
    list_dets.append(current)

    # process dets
    list_dets = [tuple(sorted(d)) for d in list_dets]

    return list_dets


def decomposed_logicals(dem_instr: stim.DemInstruction) -> list[tuple[int, ...]]:
    if dem_instr.type != "error":
        raise ValueError(f"DemInstruction is not an error, it is {dem_instr.type}.")

    list_logs = []
    current = []
    for e in dem_instr.targets_copy():
        if e.is_separator():
            list_logs.append(current)
            current = []
        if e.is_logical_observable_id():
            current.append(e.val)
    list_logs.append(current)

    # process dets
    list_logs = [tuple(sorted(l)) for l in list_logs]

    return list_logs


def from_stim_to_dem(
    stim_dem: stim.DetectorErrorModel, load_decompositions: bool = True
) -> DEM:
    """Returns the ``DEM`` object corresponding to the given
    ``stim.DetectorErrorModel`` with error decompositions.

    Parameters
    ----------
    stim_dem
        Stim's detector error model.
    load_decompositions
        If True, loads the stim decompositions to ``DEM``.

    Returns
    -------
    dem
        ``DEM`` corresponding to ``stim_dem``.
    """
    if not isinstance(stim_dem, stim.DetectorErrorModel):
        raise TypeError(f"'stim_dem' is not a stim DEM, but a {type(stim_dem)}.")

    dem = DEM()
    decomposed = {}

    for dem_instr in stim_dem.flattened():
        if dem_instr.type != "error":
            continue

        detectors = get_detectors(dem_instr)
        logicals = get_logicals(dem_instr)
        prob = dem_instr.args_copy()[0]
        id_ = dem.add_fault(prob, detectors, logicals)

        if has_separator(dem_instr):
            # needs to be processed once all the faults have been added to DEM
            decomposed[id_] = dem_instr
        else:
            if len(detectors) <= 2:
                dem.set_as_primitive(id_)

    if not load_decompositions:
        return dem

    for id_, dem_instr in decomposed.items():
        list_dets = decomposed_detectors(dem_instr)
        decom_ids = [dem.det_to_id.get(dets) for dets in list_dets]

        if None in decom_ids:
            raise ValueError(f"Decomposition uses unkown faults:\n{dem_instr}")
        if any([not dem.is_primitive(i) for i in decom_ids]):
            raise ValueError(f"Found wrong decomposition:\n{dem_instr}")

        dem.add_decomposition(id_, decom_ids)

    return dem


def from_dem_to_stim(dem: DEM) -> stim.DetectorErrorModel:
    """Returns a ``stim.DetectorErrorModel`` from a ``DEM``."""
    if not isinstance(dem, DEM):
        raise TypeError(f"'dem' is not a DEM, but a {type(dem)}.")

    stim_dem = stim.DetectorErrorModel()
    for id_ in dem.ids:
        prob = dem.probs[id_]

        if id_ in dem.decompositions:
            decomposition = dem.decompositions[id_]
            dets = [dem.detectors[i] for i in decomposition]
            logs = [dem.logicals[i] for i in decomposition]
        else:
            dets = [dem.detectors[id_]]
            logs = [dem.logicals[id_]]

        targets = []
        for k, (d, l) in enumerate(zip(dets, logs)):
            targets += [stim.target_relative_detector_id(i) for i in d]
            targets += [stim.target_logical_observable_id(i) for i in l]
            # add "^" separator except for the last element
            if k != len(dets) - 1:
                targets.append(stim.target_separator())

        dem_instr = stim.DemInstruction("error", args=[prob], targets=targets)
        stim_dem.append(dem_instr)

    return stim_dem
