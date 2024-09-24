from hyper_decom import DEM


def test_DEM():
    my_dem = DEM()
    my_dem.add_fault(0.1, [0, 1], [10, 1])
    my_dem.set_as_primitive(0)
    return
