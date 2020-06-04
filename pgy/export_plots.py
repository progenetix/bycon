from os import path as pgxp
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

################################################################################

def plot_callset_stats(**kwargs):

    dataset_id = kwargs[ "dataset_id" ]
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

    cnvstatsplot = pgxp.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ dataset_id, label, statsno_str, "cnvstats.png" ]) )
    plt.interactive( False )
    f = plt.figure( )
    gs = gridspec.GridSpec( 1, 2, width_ratios=[ 4, 1 ] )
    plt.subplot(gs[0])
    plt.xlabel( 'DUP Genome Fraction' )
    plt.ylabel( 'DEL Genome Fraction' )
    plt.ylim( (0, 1) )
    plt.xlim( (0, 1) )
    plt.text( 0.5, 0.85, statsno_str+" "+dataset_id+" callsets" )
    plt.scatter(callset_stats["dup_fs"], callset_stats["del_fs"], marker="o", s=2, alpha=float(kwargs[ "config" ]["plot_pars"][ "dotalpha" ]) )
    plt.subplot(gs[1])
    plt.ylabel( 'CNV Genome Fraction' )
    plt.ylim( (0, 1) )
    plt.violinplot( callset_stats["cnv_fs"] )
    plt.tight_layout( )
    # plt.show(block=True)
    plt.savefig( cnvstatsplot )
    print(statsno_str+" callset stats were written to "+cnvstatsplot)

