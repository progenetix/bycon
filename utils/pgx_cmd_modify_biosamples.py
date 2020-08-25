#!/usr/local/bin/python3

import yaml, re
from os import path as path
from os import system
from sys import path as sys_path
import argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys_path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *
from pgy import *

"""podmd

The script uses the `-f` parameter with a start-anchored prefixed ontology id
to retrieve samples, and then to update the prefix-determined biocharacteristics.

This isn't a "general use" function but requires some diligent use ...

Changing this to make use of direct Python data manipulation using the standard
`bycon` query generation/exacution would be possible; however, the greater
execution transparency seems to be an advantage for now.

##### Examples

* `pgx_cmd_modify_biosamples.py -d progenetix -f "icdom-97323" -i "icdot-C42.1" -l "Bone marrow"`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-i", "--id", help="id to be replaced")
    parser.add_argument("-l", "--label", help="label to be replaced")
    parser.add_argument("-d", "--datasetid", help="dataset")
    parser.add_argument("-s", "--skipquestion", action='store_true', help="skip confirmation")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-b", "--brutalmatch", action='store_true', help="forces search on the filter value, skipping the format check")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )

    args = _get_args()

    if args.alldatasets:
        dataset_ids = config[ "dataset_ids" ]
    else:
        dataset_ids =  [ args.datasetid ]
        if not dataset_ids[0] in config[ "dataset_ids" ]:
            print("No existing dataset was provided with -d ...")
            exit()

    """podmd
    The `"mongostring": True` setting leads to the query being prepared as
    _MongoDB_ string literal, instead of a dictionary for `pymongo` use.
    podmd"""

    kwargs = {
        "config": config,
        "args": args,
        "mongostring": True,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ) 
    }

    if args.brutalmatch:
        kwargs.update( { "filters": args.filters.split(',') } )
        kwargs.update( { "exact_match": True } )
    else:
        kwargs.update( { "filters": parse_filters(**kwargs) } )

    if len(kwargs["filters"]) < 1:
        print('Pleace define a proper filter value (prefixed code, e.g. "icdom-81703").')
        exit()

    kwargs.update( { "queries": update_queries_from_filters( { "queries": { } }, **kwargs) } )

    for ds_id in dataset_ids:
        _process_update_commands(ds_id, **kwargs)

################################################################################

def _process_update_commands(ds_id, **kwargs):
    
    if not kwargs["args"].skipquestion:
        if not confirm_prompt("""Update Biosamples in {}:

??? samples with "{}" 
=> new biocharacteristics id:       {}
=> new biocharacteristics label:    {}

""".format(ds_id, kwargs["args"].filters, kwargs["args"].id, kwargs["args"].label), False):
            exit()

    print("""=> updating biosamples in {}
""".format(ds_id))

    split_v = re.compile(r'^(\w+?)[\:\-](\w[\w\.]+?)$')
    pre, code = split_v.match( kwargs["args"].id ).group(1, 2)

    """podmd
    In a first instance, biocharacteristics are updated by replacing the one
    with a matching prefix.
    podmd"""

    q_string = kwargs["queries"]["biosamples"]

    mcmd = 'mongo '+ds_id+' --eval \'db.biosamples.update( '+q_string+',{ $set: { "biocharacteristics.$[elem].type.id" : "'+kwargs["args"].id+'", "biocharacteristics.$[elem].type.label" : "'+kwargs["args"].label+'" } }, { multi: true, arrayFilters: [ { "elem.type.id": { $regex: /^'+pre+'/ } } ] } )\''

    print("""
=> running MongoDB update:
    {}

""".format(mcmd))
    system(mcmd)

    """podmd
    Since sometimes no biocharacteristic with matching prefix may exist, in
    a second step such samples receive a new one.
    podmd"""

    mcmd = 'mongo '+ds_id+' --eval \'db.biosamples.update( { $and: [ '+q_string+', { "biocharacteristics.type.id": { $not: { $regex: /^'+pre+'/ } } } ] }, { $push: { "biocharacteristics" : { "type": { "id": "'+kwargs["args"].id+'", "label" : "'+kwargs["args"].label+'" } } } }, { multi: true } )\''

    print("""

=> running MongoDB update:
    {}

""".format(mcmd))
    system(mcmd)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
