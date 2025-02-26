from bycon import *
from byconServiceLibs import ByconDatatableExporter


def sampletable():
    """
    The service uses the standard bycon data retrieval pipeline with `biosample`
    as entity type. Therefore, all standard Beacon query parameters work and also
    the path is interpreted for an biosample `id` value if there is an entry at
    `.../sampletable/{id}`

    The table type can be changed with `tableType=individuals` (or `analyses`).

    #### Examples

    * http://progenetix.org/services/sampletable/pgxbs-kftvjv8w
    * http://progenetix.org/services/sampletable?datasetIds=cellz&filters=cellosaurus:CVCL_0030
    * http://progenetix.org/services/sampletable?filters=pgx:icdom-81703
    """
    fd = ByconResultSets().get_flattened_data()
    ByconDatatableExporter(fd).stream_datatable()
