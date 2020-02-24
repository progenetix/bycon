import getopt

def get_cmd_args(argv):
    try:
        opts, args = getopt.getopt(argv, "hd:b:e:j:a:", [ "dataset_id=" "bioclass=", "extid=", "jsonqueries=", "dotalpha=" ] )
    except getopt.GetoptError:
        print( 'options error' )
        sys.exit( 2 )
    
    return(opts, args)

########################################################################################################################

def pgx_datapars_from_args(opts, **kwargs):

    data_pars = kwargs[ "config" ][ "data_pars" ]
    for opt, arg in opts:
        if opt in ("-d", "--dataset_id"):
            data_pars[ "dataset_id" ] = arg

    return data_pars

########################################################################################################################

def plotpars_from_args(opts, **kwargs):

    plot_pars = kwargs[ "config" ][ "plot_pars" ]
    for opt, arg in opts:
        if opt in ("-a", "--dotalpha"):
            plot_pars[ "dotalpha" ] = arg

    return plot_pars


