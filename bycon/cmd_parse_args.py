import getopt, sys, json
from rich.console import Console
from rich.markdown import Markdown
from os import path as path

dir_path = path.dirname(path.abspath(__file__))
help_file = path.join(path.abspath(dir_path), '..', "doc", "pgxport.md")

def get_cmd_args(argv):

    try:
        opts, args = getopt.getopt(argv, "hd:b:e:j:a:", [ "help", "dataset_id=" "bioclass=", "extid=", "jsonqueries=", "dotalpha=" ] )
    except getopt.GetoptError:
        with open(help_file) as help:
	        help_doc = help.read()
        console = Console()
        markdown = Markdown("\n# Incorrect command line options - please see below\n\n"+help_doc)
        console.print(markdown)
        sys.exit( 2 )

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            with open(help_file) as help:
                help_doc = help.read()
            console = Console()
            markdown = Markdown(help_doc)
            console.print(markdown)
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

########################################################################################################################

def pgx_queries_from_args(opts, **kwargs):

    queries = { }

    for opt, arg in opts:
        if opt in ("-j", "--jsonqueries"):
            queries = json.loads(arg)
        else:
            querylist = []
            if opt in ("-b", "--bioclass"):
                querylist.append({"biocharacteristics.type.id": {"$regex": arg } })
            if opt in ("-e", "--extid"):
                querylist.append( { "external_references.type.id": { "$regex": arg } } )
            if len(querylist) > 1:
                queries["biosamples"] = {"$and": querylist }
            elif len(querylist) == 1:
                queries["biosamples"] = querylist[0]
    return queries
