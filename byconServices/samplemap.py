from bycon import BYC_PARS, ByconResultSets, prdbug
from byconServiceLibs import ByconMap

def samplemap():
    """
    ==TBD==
    """
    BYC_PARS.update({"marker_type": "marker"})
    fd = ByconResultSets().get_flattened_data()
    BM = ByconMap()
    BM.add_data_from_datasets(fd)
    BM.printMapHTML()

