from os import path
from pathlib import Path

from bycon import BYC, BYC_PARS, ByconResultSets, prdbug
from byconServiceLibs import (
    ByconBundler,
    ByconPlot, 
    ByconPlotPars,
    ExportFile
)

################################################################################

def sampleplots():
    """
    The plot service uses the standard bycon data retrieval pipeline with `biosample`
    as entity type. Therefore, all standard Beacon query parameters work and also
    the path is interpreted for an biosample `id` value if there is an entry at
    `.../sampleplots/{id}`

    The plot type can be set with `plotType=samplesplot` (or `histoplot` but that is
    the fallback). Plot options are available as usual.

    #### Examples (using the Progenetix resource as endpoint):

    * http://progenetix.org/services/sampleplots/pgxbs-kftvjv8w
    * http://progenetix.org/services/sampleplots/pgxbs-kftvjv8w?plotType=samplesplot&datasetIds=cellz
    * http://progenetix.org/services/sampleplots?plotType=samplesplot&datasetIds=cellz&filters=cellosaurus:CVCL_0030
    * http://progenetix.org/services/sampleplots?filters=pgx:icdom-81703
    * http://progenetix.org/services/sampleplots/?testMode=true&plotType=samplesplot
    * http://progenetix.org/services/sampleplots?filters=pgx:icdom-81703&plotType=histoplot&plotPars=plot_chro_height=0::plot_title_font_size=0::plot_area_height=18::plot_margins=0::plot_axislab_y_width=0::plot_grid_stroke=0::plot_footer_font_size=0::plot_width=400
    * http://progenetix.org/services/sampleplots?datasetIds=progenetix&plotMinLength=1000&plotMaxLength=3000000&geneId=CDKN2A&variantType=EFO:0020073&plotPars=plotChros=9::plotGeneSymbols=CDKN2A::plotWidth=300&plotType=histoplot
    """
    file_id = str(BYC_PARS.get("file_id", "___no-input-file___"))
    inputfile = Path( path.join( *BYC["env_paths"][ "server_tmp_dir_loc" ], file_id ) )

    BB = ByconBundler()
    if inputfile.is_file():
        pdb = BB.pgxseg_to_plotbundle(inputfile)
    else:
        RSS = ByconResultSets().datasetsResults()
        pdb = BB.resultsets_frequencies_bundles(RSS)
        # getting the variants for the samples is time consuming so only optional
        if "samples" in ByconPlotPars().plotType():
            pdb.update( ByconBundler().resultsets_analysis_bundles(RSS) )
    BP = ByconPlot(pdb)
    if (svg_f := ExportFile("svg").check_outputfile_path()):
        BP.svg2file(svg_f)
    else:
        BP.svgResponse()

