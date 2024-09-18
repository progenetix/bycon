#!/usr/bin/env python3
import sys, traceback
from os import path
from pathlib import Path

from bycon import *

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from bycon_bundler import ByconBundler
from bycon_plot import *
from file_utils import ExportFile
from interval_utils import generate_genome_bins

"""
The plot service uses the standard bycon data retrieval pipeline with `biosample`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../sampleplots/{id}`

The plot type can be set with `plotType=samplesplot` (or `histoplot` but that is
the fallback). Plot options are available as usual.

* http://progenetix.org/services/sampleplots/pgxbs-kftvjv8w
* http://progenetix.org/services/sampleplots/pgxbs-kftvjv8w?plotType=samplesplot&datasetIds=cellz
* http://progenetix.org/services/sampleplots?plotType=samplesplot&datasetIds=cellz&filters=cellosaurus:CVCL_0030
* http://progenetix.org/services/sampleplots?filters=pgx:icdom-81703
* http://progenetix.org/services/sampleplots/?testMode=true&plotType=samplesplot
* http://progenetix.org/services/sampleplots?filters=pgx:icdom-81703&plotType=histoplot&plotPars=plot_chro_height=0::plot_title_font_size=0::plot_area_height=18::plot_margins=0::plot_axislab_y_width=0::plot_grid_stroke=0::plot_footer_font_size=0::plot_width=400
* http://progenetix.org/services/sampleplots?datasetIds=progenetix&plotMinLength=1000&plotMaxLength=3000000&geneId=CDKN2A&variantType=EFO:0020073&plotPars=plotChros=9::plotGeneSymbols=CDKN2A::plotWidth=300&plotType=histoplot
"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        sampleplots()
    except Exception:
        print_text_response(traceback.format_exc(), 302)


################################################################################

def sampleplots():
    BYC.update({
        "request_entity_path_id": "biosamples",
        "request_entity_id": "biosample"
    })
    initialize_bycon_service()
    # BYC.update({"response_entity_id": "biosample"})
    generate_genome_bins()

    if not (plot_type := BYC_PARS.get("plot_type")):
        plot_type = "histoplot"

    file_id = BYC_PARS.get("file_id", "___no-input-file___")
    inputfile = Path( path.join( *BYC["local_paths"][ "server_tmp_dir_loc" ], file_id ) )

    pb = ByconBundler()
    if inputfile.is_file():
        pdb = pb.pgxseg_to_plotbundle(inputfile)
    else:
        RSS = ByconResultSets().datasetsResults()
        pdb = pb.resultsets_frequencies_bundles(RSS)

        # getting the variants for the samples is time consuming so only optional
        if "samples" in plot_type:
            pdb.update( ByconBundler().resultsets_callset_bundles(RSS) )

    svg_f = ExportFile("svg").checkOutputFile()
    BP = ByconPlot(pdb)
    if svg_f:
        BP.svg2file(svg_f)
    else:
        BP.svgResponse()


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
