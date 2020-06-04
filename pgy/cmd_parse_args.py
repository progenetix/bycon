import sys, json
from rich.console import Console
from rich.markdown import Markdown
import re

# dir_path = path.dirname(path.abspath(__file__))
# help_file = path.join(path.abspath(dir_path), '..', "doc", "pgxport.md")

################################################################################

def plotpars_from_args(**kwargs):

    args = kwargs[ "args" ]
    plot_pars = kwargs[ "config" ][ "plot_pars" ]
    if args.dotalpha:
        plot_pars[ "dotalpha" ] = args.dotalpha

    return plot_pars

################################################################################

def pgx_queries_from_js(**kwargs):

    queries = { }
    args = kwargs[ "args" ]
    
    if args.queries:

        if "queries" not in kwargs:
            print("Please provide either filter values (`-f`) or a JSON query object (`-q).")
            sys.exit()

        q_s = args.queries
        q_s = re.sub( r"([\{\s])(\$\w+?)([\:\s])", r'\1"\2"\3', q_s)
        q_s = re.sub( r"\"\$regex\"\:\s*?\/([^\/]+?)\/", r'"$regex":"\1"', q_s)
        # print(q_s)

        queries = json.loads(q_s)

    elif "queries" in kwargs:

        return kwargs[ "queries" ]

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

