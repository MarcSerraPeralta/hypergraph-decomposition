from __future__ import annotations
from collections.abc import Iterable
import warnings

from .util import xor_lists, xor_two_probs


class DEM:
    def __init__(self) -> None:
        self.ids: list[int] = []
        self.probs: dict[int, float | int] = {}
        self.detectors: dict[int, tuple[int, ...]] = {}
        self.det_to_id: dict[tuple[int, ...], int] = {}
        self.logicals: dict[int, tuple[int, ...]] = {}
        self.decompositions: dict[int, tuple[int, ...]] = {}
        self.primitives: list[int] = []
        self.prim_det_to_id: dict[tuple[int, ...], int] = {}
        self.decomposed: dict[int, bool] = {}
        return

    def add_fault(self, prob: float | int, dets: Iterable, logs: Iterable) -> int:
        """Adds a fault (or error mechanism) to the DEM.

        Parameters
        ----------
        prob
            Probability of the fault.
        dets
            Detectors triggered by the fault.
        logs
            Logical observables flipped by the fault.

        Returns
        -------
        id_
            Fault id.
        """
        if not (isinstance(prob, float) or isinstance(prob, int)):
            raise TypeError(f"'prob' must be float, but {type(prob)} was given.")
        if prob > 1 or prob < 0:
            raise ValueError(f"Probabilities must be inside [0,1], not {prob}.")
        if not isinstance(dets, Iterable):
            raise TypeError(f"'det' must be sized, but {type(dets)} was given.")
        if not isinstance(logs, Iterable):
            raise TypeError(f"'logs' must be sized, but {type(logs)} was given.")

        # prepare the detectors and logs
        dets, logs = tuple(sorted(dets)), tuple(sorted(logs))

        # check existance of same faults
        if (same_id := self.det_to_id.get(dets)) is not None:
            if self.logicals[same_id] != logs:
                raise ValueError(
                    "A fault in this DEM triggers the same detectors "
                    f"but has different logical effect, id={same_id}"
                )
            else:
                self.probs[same_id] = xor_two_probs(self.probs[same_id], prob)
                return same_id

        # create new fault with a new id
        id_ = len(self.ids)
        self.ids.append(id_)
        self.probs[id_] = prob
        self.detectors[id_] = dets
        self.logicals[id_] = logs
        self.det_to_id[dets] = id_
        self.decomposed[id_] = False
        return id_

    def set_as_primitive(self, id_: int) -> None:
        """Flags a fault (or error mechanism) as primitive, meaning that
        it only triggers at most two detectors.

        Parameters
        ----------
        id_
            Fault id.
        """
        if id_ not in self.ids:
            raise ValueError(f"'id={id_}' is not an id from this DEM.")
        if len(self.detectors[id_]) > 2:
            raise ValueError(f"Primitive faults must have weight-2 or less.")

        if id_ not in self.primitives:
            self.primitives.append(id_)
            detectors = self.detectors[id_]
            self.prim_det_to_id[detectors] = id_
            self.decomposed[id_] = True

        return

    def is_primitive(self, id_: int) -> bool:
        """Returns if fault is primitive."""
        return id_ in self.primitives

    def add_decomposition(
        self,
        id_: int,
        decomposition: Iterable[int],
        ignore_logical_error: bool = False,
        override: bool = False,
    ) -> None:
        """Add a decomposition for a given fault (or error mechanism).

        Parameters
        ----------
        id_
            Fault to which add the decomposition.
        decomposition
            List of the fault ids in which ``id_`` is decomposed into.
        ignore_logical_error
            If True, does not raise an error if the logical effect of the
            provided decomposition does not match the logical effect of ``id_``.
        override
            If True, sets the given decomposition even if the speficied fault
            already had a decomposition.
        """
        if id_ not in self.ids:
            raise ValueError(f"'id={id_}' is not an id from this DEM.")
        if self.decomposed[id_] and (not override):
            raise ValueError(
                f"'id={id_}' already has a decomposition (use 'override')."
            )
        if not isinstance(decomposition, Iterable):
            raise TypeError(
                f"'decomposition' must be iterable, but {type(decomposition)} was given."
            )
        if any([not self.is_primitive(i) for i in decomposition]):
            raise ValueError(
                "All elements in the decomposition must be primitive faults, "
                f"but {decomposition} were given."
            )
        if self.is_primitive(id_):
            raise ValueError(f"Cannot add decomposition to primitive fault id={id_}.")

        h_dets = self.detectors[id_]
        h_logs = self.logicals[id_]
        e_dets = tuple(self.detectors[i] for i in decomposition)
        e_logs = tuple(self.logicals[i] for i in decomposition)

        if xor_lists(*e_dets) != h_dets:
            raise ValueError(
                "Decomposition has different detectors than hyperedge"
                f"\nhyperedge({id_})={h_dets}\ndecomposition({decomposition})={xor_lists(*e_dets)}"
            )

        if xor_lists(*e_logs) != h_logs:
            if not ignore_logical_error:
                raise ValueError(
                    "Decomposition has a different logical effect than hyperedge"
                    f"\nhyperedge({id_})={h_logs}\ndecomposition({decomposition})={xor_lists(*e_logs)}"
                )

            warnings.warn(
                f"The logical effect of fault id={id_} is different "
                f"than its decomposition: {decomposition}"
            )
            self.decomposed[id_] = True
            return

        # add decomposition
        self.decompositions[id_] = tuple(decomposition)
        self.decomposed[id_] = True
        return

    def get_primitive_graph(self) -> DEM:
        """Returns a DEM containing only the primitive faults with
        their corresponding probabilities."""
        dem = DEM()
        for id_ in self.primitives:
            new_id = dem.add_fault(
                self.probs[id_], self.detectors[id_], self.logicals[id_]
            )
            dem.set_as_primitive(new_id)
        return dem

    def get_decomposed_dem(self) -> DEM:
        """Returns a DEM containing only the primitive faults with their
        probabilities updated from the hyperedges."""
        if len(self.get_undecomposed_faults()) != 0:
            raise ValueError(
                "There are some undecomposed hyperedges (use 'get_undecomposed_faults')."
            )

        dem = self.get_primitive_graph()
        for id_ in self.ids:
            if id_ in self.primitives:
                continue

            for i in self.decompositions[id_]:
                prob = self.probs[id_]
                dets = self.detectors[i]
                logs = self.logicals[i]
                dem.add_fault(prob, dets, logs)

        return dem

    def get_undecomposed_faults(self) -> list[int]:
        """Returns a list of faults ids for the undecomposed faults."""
        faults = [k for k, v in self.decomposed.items() if not v]
        return faults

    def is_matching_graph(self):
        """Returns if the decomposed DEM is a matching graph."""
        for id_ in self.get_undecomposed_faults():
            if len(self.detectors[id_]) > 2:
                return False
        return True

    def get_info_fault(self, id_: int) -> dict[str, object]:
        """Returns a dictionary with all the data corresponding to the given fault."""
        data = {
            "id": id_,
            "detectors": self.detectors[id_],
            "logicals": self.logicals[id_],
            "prob": self.probs[id_],
            "is_primitive": id_ in self.primitives,
            "decomposition": (
                self.decompositions[id_] if id_ in self.decompositions else None
            ),
        }
        return data
