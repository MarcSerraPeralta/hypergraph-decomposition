from collections.abc import Iterable


def xor_two_lists(list1: Iterable, list2: Iterable) -> tuple:
    return tuple(sorted(list(set(list1).symmetric_difference(list2))))


def xor_lists(*elements: Iterable) -> tuple:
    output = []
    for element in elements:
        output = xor_two_lists(output, element)
    return tuple(sorted(output))


def xor_two_probs(p: float | int, q: float | int) -> float | int:
    return p * (1 - q) + (1 - p) * q
