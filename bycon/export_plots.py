from os import path as pgxp
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

################################################################################

def plot_callset_stats(**kwargs):

    dataset_id = kwargs[ "config" ][ "data_pars" ][ "dataset_id" ]
    dash = kwargs[ "config" ][ "const" ][ "dash_sep" ]

    statsno_str = str(len(kwargs[ "callsets_stats" ]["cnv_fs"]))

    cnvstatsplot = pgxp.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, statsno_str, "cnvstats.png" ]) )
    plt.interactive( False )
    f = plt.figure( )
    gs = gridspec.GridSpec( 1, 2, width_ratios=[ 4, 1 ] )
    plt.subplot(gs[0])
    plt.xlabel( 'DUP Genome Fraction' )
    plt.ylabel( 'DEL Genome Fraction' )
    plt.ylim( (0, 1) )
    plt.xlim( (0, 1) )
    plt.text( 0.5, 0.85, str(len(kwargs[ "callsets_stats" ]["cnv_fs"]))+" "+dataset_id+" callsets" )
    plt.scatter(kwargs[ "callsets_stats" ]["dup_fs"], kwargs[ "callsets_stats" ]["del_fs"], marker="o", s=2, alpha=float(kwargs[ "config" ]["plot_pars"][ "dotalpha" ]) )
    plt.subplot(gs[1])
    plt.ylabel( 'CNV Genome Fraction' )
    plt.ylim( (0, 1) )
    plt.violinplot( kwargs[ "callsets_stats" ]["cnv_fs"] )
    plt.tight_layout( )
    # plt.show(block=True)
    plt.savefig( cnvstatsplot )
    print(statsno_str+" callset stats were written to "+cnvstatsplot)

