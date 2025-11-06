from bycon import BYC_PARS, ByconResultSets, prdbug
from byconServiceLibs import ByconMap


def sampleglobe():
    """
    ==TBD==
    * https://progenetix.org/services/sampleglobe?geoLatitude=25.05&geoLongitude=121.53&geoDistance=2000000&filters=NCIT:C8614
    * https://progenetix.org/services/sampleglobe?datasetIds=progenetix&filters=NCIT:C9335&&plotPars=markerType:circle::marker_scale:8&limit=0
    """
    BYC_PARS.update({"marker_type": "marker"})
    fd = ByconResultSets().get_flattened_data()
    BM = ByconMap()
    BM.add_data_from_datasets(fd)
    BM.printGlobeHTML()

