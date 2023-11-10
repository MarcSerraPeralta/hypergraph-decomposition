def xor(list1, list2):
    return sorted(list(set(list1).symmetric_difference(list2)))


def multiple_xor(elements):
    output = []
    for element in elements:
        output = xor(output, element)
    return sorted(output)


def g(p, q):
    return p * (1 - q) + (1 - p) * q


class DEM:
    def __init__(self):
        self._current_id = 0
        self.ids = []
        self.probs = {}
        self.detectors = {}
        self.det_to_id = {}
        self.logicals = {}
        self.decompositions = {}
        self.primitives = []
        self.prim_det_to_id = {}
        self.undecomposed = {}
        return

    def add_fault(self, prob, dets, logs):
        # data type checks
        if prob > 1 or prob < 0:
            raise ValueError(f"Probabilities must be inside [0,1], not {prob}")

        # check existance of same faults
        dets = sorted(dets)
        logs = sorted(logs)
        if same_id := self._find_same_fault_id(dets):
            if self.logicals[same_id] != logs:
                raise ValueError(
                    f"Found fault that has the same detectors but different logical effect, id={same_id}"
                )
            else:
                # update probability
                self.probs[same_id] = g(self.probs[same_id], prob)
                return same_id

        # create new fault
        id_ = self._current_id
        self._current_id += 1
        self.ids.append(id_)
        self.probs[id_] = prob
        self.detectors[id_] = sorted(dets)  # for comparison
        self.logicals[id_] = sorted(logs)  # for comparison
        self.det_to_id[tuple(sorted(dets))] = id_
        # removing elements from a dictionary is faster than from a list
        self.undecomposed[id_] = True
        return id_

    def add_primitive(self, id_):
        # check if the fault can be a primitve
        if len(self.detectors[id_]) > 2:
            raise ValueError(
                f"Primitive edges must have weight-2 or less (id={id_} does not fulfill this condition)"
            )

        # add to primitive, if not already present
        if id_ not in self.primitives:
            self.primitives.append(id_)
            detectors = tuple(self.detectors[id_])
            self.prim_det_to_id[detectors] = id_
            del self.undecomposed[id_]
        return

    def add_decomposition(self, id_, decomposition):
        # check validity of decomposition
        h_dets = self.detectors[id_]
        h_logs = self.logicals[id_]
        e_dets = [self.detectors[i] for i in decomposition]
        e_logs = [self.logicals[i] for i in decomposition]

        if multiple_xor(e_dets) == h_dets:
            if multiple_xor(e_logs) != h_logs:
                raise ValueError(
                    (
                        "Decomposition has a different logical effect than hyperedge",
                        f"\nhyperedge({id_})={h_logs}\ndecomposition({decomposition}={e_logs})",
                    )
                )
        else:
            raise ValueError(
                (
                    "Decomposition has different detectors than hyperedge",
                    f"\nhyperedge({id_})={h_dets}\ndecomposition({decomposition}={e_dets})",
                )
            )

        # add decomposition
        if id_ in self.decompositions:
            self.decompositions[id_].append(decomposition)
        else:
            self.decompositions[id_] = [decomposition]
        del self.undecomposed[id_]
        return

    def get_primitive_graph(self):
        dem = DEM()
        for id_ in self.primitives:
            dem.add_fault(self.probs[id_], self.detectors[id_], self.logicals[id_])
        return dem

    def get_decomposed_graph(self):
        undecom_hyperedges = self.get_undecomposed_hyperedges()
        if len(undecom_hyperedges) != 0:
            raise ValueError(
                f"There are some undecomposed hyperedges:\n{undecom_hyperedges}"
            )

        dem = DEM()
        for id_ in self.ids:
            if len(self.detectors[id_]) > 2:
                decom_ids = self.decompositions[id_]
                if len(decom_ids) != 1:
                    raise ValueError(f"There are multiple decompositions for id={id_}")
                ids_to_add = decom_ids[0]
            else:
                ids_to_add = [id_]

            for i in ids_to_add:
                prob = self.probs[id_]
                dets = self.detectors[i]
                logs = self.logicals[i]
                dem.add_fault(prob, dets, logs)
        return dem

    def get_undecomposed_hyperedges(self):
        return self.undecomposed

    def is_matching_graph(self):
        for id_ in self.undecomposed:
            if len(self.detectors[id_]) > 2:
                return False
        return True

    def get_info_fault(id_):
        data = {
            "id": id_,
            "detectors": self.detectors[id_],
            "logicals": self.logicals[id_],
            "prob": self.probs[id_],
            "is_primitive": id_ in self.primitives,
            "decomposition": self.decompositions[id_]
            if id_ in self.decompositions[id_]
            else None,
        }
        return data

    def _find_same_fault_id(self, other_dets):
        other_dets = tuple(sorted(other_dets))
        return self.det_to_id.get(other_dets, False)
