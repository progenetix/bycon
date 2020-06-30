from os import path as pgxp
from pymongo import MongoClient
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

################################################################################

def callsets_return_stats(ds_id, **kwargs):

    query = { "_id": { "$in": kwargs["query_results"][ "cs._id" ][ "target_values" ] } }
    ds_id = kwargs["query_results"][ "bs._id" ][ "source_db" ]

    cs_coll = MongoClient( )[ ds_id ][ "callsets" ]

    cs_stats = { }
    cs_stats["dup_fs"] = []
    cs_stats["del_fs"] = []
    cs_stats["cnv_fs"] = []

    for cs in cs_coll.find( query ) :
        if "cnvstatistics" in cs["info"]:
            if "dupfraction" in cs["info"]["cnvstatistics"] and "delfraction" in cs["info"]["cnvstatistics"]:
                cs_stats["dup_fs"].append(cs["info"]["cnvstatistics"]["dupfraction"])
                cs_stats["del_fs"].append(cs["info"]["cnvstatistics"]["delfraction"])
                cs_stats["cnv_fs"].append(cs["info"]["cnvstatistics"]["cnvfraction"])

    return cs_stats

################################################################################

def plot_callset_stats(ds_id, **kwargs):

    args = kwargs[ "args" ]
    callset_stats = kwargs[ "callsets_stats" ]
    statsno = len(callset_stats['cnv_fs'])
    if not statsno:
        print('There is zero callset to be ploted.')
        return

    label = ""
    if args.label:
        label = args.label
    statsno_str = str(statsno)

    cnvstatsplot = pgxp.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ ds_id, label, statsno_str, "cnvstats.png" ]) )
    plt.interactive( False )
    f = plt.figure( )
    gs = gridspec.GridSpec( 1, 2, width_ratios=[ 4, 1 ] )
    plt.subplot(gs[0])
    plt.xlabel( 'DUP Genome Fraction' )
    plt.ylabel( 'DEL Genome Fraction' )
    plt.ylim( (0, 1) )
    plt.xlim( (0, 1) )
    plt.text( 0.5, 0.85, statsno_str+" "+ds_id+" callsets" )
    plt.scatter(callset_stats["dup_fs"], callset_stats["del_fs"], marker="o", s=2, alpha=float(kwargs[ "config" ]["plot_pars"][ "dotalpha" ]) )
    plt.subplot(gs[1])
    plt.ylabel( 'CNV Genome Fraction' )
    plt.ylim( (0, 1) )
    plt.violinplot( callset_stats["cnv_fs"] )
    plt.tight_layout( )
    # plt.show(block=True)
    plt.savefig( cnvstatsplot )
    print(statsno_str+" callset stats were written to "+cnvstatsplot)

