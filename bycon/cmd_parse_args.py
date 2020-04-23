import getopt, sys, json
from rich.console import Console
from rich.markdown import Markdown
from os import path as path

dir_path = path.dirname(path.abspath(__file__))
help_file = path.join(path.abspath(dir_path), '..', "doc", "pgxport.md")

def get_cmd_args():

    argv = sys.argv[ 1: ]

    try:
        opts, args = getopt.getopt(argv, "htd:b:e:j:a:f:p:y:c:o:g:", [ "help", "dataset_id=" "bioclass=", "extid=", "jsonqueries=", "dotalpha=", "mappingfile=", "outpath=", "icdomappath=", "cytoBands=", "chroBases=", "genome=" ] )
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

################################################################################

def pgx_datapars_from_args(opts, **kwargs):

    data_pars = kwargs[ "config" ][ "data_pars" ]
    for opt, arg in opts:
        if opt in ("-d", "--dataset_id"):
            data_pars[ "dataset_id" ] = arg

    return data_pars

################################################################################

def plotpars_from_args(opts, **kwargs):

    plot_pars = kwargs[ "config" ][ "plot_pars" ]
    for opt, arg in opts:
        if opt in ("-a", "--dotalpha"):
            plot_pars[ "dotalpha" ] = arg

    return plot_pars

################################################################################

def pgx_queries_from_args(opts):

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

################################################################################

def confirm_prompt(prompt=None, resp=False):

    """podmd
    ### `confirm_prompt`
    
    ... prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    """
    
    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')
        
    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print("please enter y or n.")
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

