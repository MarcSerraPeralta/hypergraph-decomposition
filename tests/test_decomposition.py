import pytest
import stim

from hyper_decom import decompose_dem


def test_decompose_dem():
    dem = stim.DetectorErrorModel(
        """
        error(0.1) D0 D1 D2 D3
        error(0.1) D0 D1 L0
        error(0.1) D2 D3 L0
        """
    )

    decom_dem = decompose_dem(dem)

    expected_dem = stim.DetectorErrorModel(
        """
        error(0.1) D0 D1 L0 ^ D2 D3 L0
        error(0.1) D0 D1 L0
        error(0.1) D2 D3 L0
        """
    )

    assert decom_dem == expected_dem

    return


def test_decompose_dem_mwpm_fail():
    dem = stim.DetectorErrorModel("error(0.1) D0 D1 D2 D3")

    with pytest.raises(ValueError):
        _ = decompose_dem(dem)

    dem = stim.DetectorErrorModel(
        """
        error(0.1) D0 D1 D2 D3
        error(0.1) D0 D1 
        error(0.1) D1 D2
        error(0.1) D3
        """
    )

    with pytest.raises(ValueError):
        _ = decompose_dem(dem)

    return
