import pytest

from hyper_decom import DEM


def test_DEM():
    my_dem = DEM()
    my_dem.add_fault(0.1, [0, 1, 2], [10, 1])
    my_dem.add_fault(0.2, [0], [1, 10])
    my_dem.add_fault(0.3, [1], [1])
    my_dem.add_fault(0.4, [2], [1])
    my_dem.set_as_primitive(1)
    my_dem.set_as_primitive(2)
    my_dem.set_as_primitive(3)

    assert not my_dem.is_matching_graph()

    with pytest.raises(ValueError):
        my_dem.set_as_primitive(0)

    assert my_dem.is_primitive(2)
    assert not my_dem.is_primitive(0)

    prim_dem = my_dem.get_primitive_graph()
    assert len(prim_dem.ids) == 3
    assert prim_dem.detectors[0] == (0,)
    assert prim_dem.logicals[0] == (1, 10)

    my_dem.add_decomposition(0, (1, 2, 3))

    with pytest.raises(Exception):
        my_dem.add_decomposition(1, (2, 3))

    assert len(my_dem.get_undecomposed_faults()) == 0

    decom_dem = my_dem.get_decomposed_dem()
    assert len(decom_dem.ids) == 3
    assert decom_dem.is_matching_graph()

    info = my_dem.get_info_fault(1)
    assert isinstance(info, dict)

    return


def test_DEM_add_decomposition_failure():
    my_dem = DEM()
    my_dem.add_fault(0.1, [0, 1], [])
    my_dem.add_fault(0.1, [0], [])
    my_dem.add_fault(0.1, [1], [])
    my_dem.set_as_primitive(0)
    my_dem.set_as_primitive(1)
    my_dem.set_as_primitive(2)

    with pytest.raises(ValueError):
        my_dem.add_decomposition(0, (1, 2))

    return
