import pytest
import stim

from hyper_decom import DEM
from hyper_decom.stim_tools import from_stim_to_dem, from_dem_to_stim


def test_from_stim_to_dem():
    stim_dem = stim.DetectorErrorModel(
        """
        error(0.1) D1 D2 ^ D2 L0
        error(0.2) D7
        error(0.3) D3 L0 ^ D4 L0
        error(0.1) D1 D2
        error(0.1) D2 L0
        error(0.1) D3 L0
        error(0.1) D4 L0 
        """
    )

    dem = from_stim_to_dem(stim_dem)

    assert len(dem.ids) == 7
    assert set(dem.primitives) == set([1, 3, 4, 5, 6])
    assert dem.detectors[0] == (1,)
    assert dem.logicals[2] == tuple()
    assert dem.logicals[0] == (0,)
    assert set(dem.decompositions[0]) == set([3, 4])
    assert set(dem.decompositions[2]) == set([5, 6])

    stim_dem = stim.DetectorErrorModel("error(0.1) D1 ^ D2")
    with pytest.raises(Exception) as _:
        _ = from_stim_to_dem(stim_dem)

    stim_dem = stim.DetectorErrorModel(
        """
        error(0.1) D1 D2 D3 ^ D2
        error(0.1) D1 D2 D3
        error(0.1) D2
        """
    )
    with pytest.raises(Exception) as _:
        _ = from_stim_to_dem(stim_dem)

    return


def test_from_dem_to_stim():
    dem = DEM()
    dem.add_fault(0.1, [0, 1], [])
    dem.add_fault(0.2, [0, 2], [1])
    dem.add_fault(0.1, [0], [2])
    dem.add_fault(0.1, [1], [2])
    dem.set_as_primitive(2)
    dem.set_as_primitive(3)
    dem.add_decomposition(0, [2, 3])

    stim_dem = from_dem_to_stim(dem)

    expected_dem = stim.DetectorErrorModel(
        """
        error(0.1) D0 L2 ^ D1 L2
        error(0.2) D0 D2 L1
        error(0.1) D0 L2
        error(0.1) D1 L2
        """
    )
    assert stim_dem == expected_dem

    return
