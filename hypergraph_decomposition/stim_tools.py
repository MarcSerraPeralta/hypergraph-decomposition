import stim

from .detector_error_model import DEM, multiple_xor


def get_detectors(dem_instr):
    if has_separator(dem_instr):
        return multiple_xor(decomposed_detectors(dem_instr))
    else:
        return [i.val for i in dem_instr.targets_copy() if i.is_relative_detector_id()]


def get_logicals(dem_instr):
    if has_separator(dem_instr):
        return multiple_xor(decomposed_logicals(dem_instr))
    else:
        return [i.val for i in dem_instr.targets_copy() if i.is_logical_observable_id()]


def has_separator(dem_instr):
    return bool(len([i for i in dem_instr.targets_copy() if i.is_separator()]))


def decomposed_detectors(dem_instr):
    list_dets = []
    current = []
    for e in dem_instr.targets_copy():
        if e.is_separator():
            list_dets.append(current)
            current = []
        if e.is_relative_detector_id():
            current.append(e.val)
    list_dets.append(current)
    return list_dets


def decomposed_logicals(dem_instr):
    list_logs = []
    current = []
    for e in dem_instr.targets_copy():
        if e.is_separator():
            list_logs.append(current)
            current = []
        if e.is_logical_observable_id():
            current.append(e.val)
    list_logs.append(current)
    return list_logs


def from_decomposed_stim_to_dem(stim_dem, ignore_bad_decompositions=False):
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
            decomposed[id_] = dem_instr

    for id_, dem_instr in decomposed.items():
        list_dets = decomposed_detectors(dem_instr)
        ids = [dem._find_same_fault_id(dets) for dets in list_dets]
        if None in ids:
            print(ids, dem.ids, dem_instr, list_dets)
            # stim decomposed wrongly the hyperedge
            # e.g. D0 ^ D1 D2 ^ L0
            if not ignore_bad_decompositions:
                raise ValueError(f"Found wrong decomposition:\n{dem_instr}")
            else:
                continue  # skip this decomposition
        true_primitives = []
        for prim_id in ids:
            if prim_id in decomposed:
                # this is not an actual primitive edge
                # this can only happen for weight-2 edges, if not it is
                # not a valid hyperedge decomposition into edges
                list_dets_2 = decomposed_detectors(decomposed[prim_id])
                ids_2 = [dem._find_same_fault_id(dets) for dets in list_dets_2]
                true_primitives += ids_2
                dem.add_primitive(ids_2[0])
                dem.add_primitive(ids_2[1])
            else:
                true_primitives.append(prim_id)
                dem.add_primitive(prim_id)
        dem.add_decomposition(id_, true_primitives)

    return dem


def from_stim_to_dem(stim_dem):
    dem = DEM()
    decomposed = {}
    for dem_instr in stim_dem.flattened():
        if dem_instr.type != "error":
            continue
        detectors = get_detectors(dem_instr)
        logicals = get_logicals(dem_instr)
        prob = dem_instr.args_copy()[0]
        id_ = dem.add_fault(prob, detectors, logicals)

    return dem


def from_dem_to_stim(dem):
    stim_dem = stim.DetectorErrorModel()
    for id_ in dem.ids:
        prob = dem.probs[id_]

        if id_ in dem.decompositions:
            decompositions = dem.decompositions[id_]
            if len(decompositions) > 1:
                raise TypeError(f"Found more than one decomposition for id={id_}")
            dets = [dem.detectors[i] for i in decompositions[0]]
            logs = [dem.logicals[i] for i in decompositions[0]]
        else:
            dets = [dem.detectors[id_]]
            logs = [dem.logicals[id_]]

        targets = []
        for k, (d, l) in enumerate(zip(dets, logs)):
            targets += [stim.target_relative_detector_id(i) for i in d]
            targets += [stim.target_logical_observable_id(i) for i in l]
            if k != len(dets) - 1:
                targets.append(stim.target_separator())

        dem_instr = stim.DemInstruction("error", args=[prob], targets=targets)
        stim_dem.append(dem_instr)
    return stim_dem
