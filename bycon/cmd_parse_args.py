import sys
from rich.console import Console
from rich.markdown import Markdown

# dir_path = path.dirname(path.abspath(__file__))
# help_file = path.join(path.abspath(dir_path), '..', "doc", "pgxport.md")

################################################################################

def plotpars_from_args(args, **kwargs):

    plot_pars = kwargs[ "config" ][ "plot_pars" ]
    if args.dotalpha:
        plot_pars[ "dotalpha" ] = args.dotalpha

    return plot_pars

################################################################################

def pgx_queries_from_args(**kwargs):

    queries = { }
    args = kwargs[ "args" ]

    if args.queries:
        queries = json.loads(args.queries)
    else:
        querylist = []
        if args.bioclass:
            querylist.append({"biocharacteristics.type.id": {"$regex": arg } })
        if args.extid:
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

