#!/usr/local/bin/python3

import sys, re, json
from ruamel.yaml import YAML
from os import path as path
from os import scandir as scandir
from os import remove as deleteFile
import argparse
import pathlib
from distutils.dir_util import copy_tree

"""podmd
The script converts yaml <-> json, either a single file or all files of a given
directory. If converting a directory, the input file type has to be specified.

* `./yamler.py -i ~/GitHub/ga4gh-beacon/beacon-v2-Models/BEACON-V2-draft4-Model/ --filetype json`
* `./yamler.py -i ~/GitHub/ga4gh-beacon/beacon-v2-Models/TEMPLATE-Model/beaconMap.json`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inpath", help="File or directory to be converted.", required=True)
    parser.add_argument("-o", "--outpath", help="Directory to be saved to.")
    parser.add_argument("-t", "--filetype", help="File type to convert from; for directory parsing.")

    return parser.parse_args()

################################################################################

def main():

    """podmd
    end_podmd"""

    supported = ["json", "yaml"]

    args = _get_args()
    inpath = pathlib.Path(args.inpath)
    clean = False

    if inpath.is_dir():
        if args.outpath:
            op = pathlib.Path(args.outpath)
            if not op.is_dir():
                print()
                print("¡¡¡ Please create the out dir first at {} !!!".format(op.as_posix()))
                exit()               
            copy_tree(inpath.as_posix(), op.as_posix())
            inpath = op
            clean = True
        convert_dir(inpath, supported, clean, args)
    elif inpath.is_file():
        convert_file(str(inpath))

################################################################################

def convert_dir(inpath, supported, clean, args):

    if not args.filetype in supported:
        print()
        print("¡¡¡ If converting a directory, one has to give a correct '--filetype': {} !!!".format(" or ".join(supported)))
        exit()
    fs = [ f.path for f in scandir(inpath) if f.is_file() ]
    for i_f in fs:
        ext = pathlib.PurePosixPath(i_f).suffix
        ext = re.sub(r'\.', "", ext)
        if ext == args.filetype:
            convert_file(i_f, clean)
        elif clean is True:
            deleteFile(i_f)

    dp = [ d.path for d in scandir(inpath) if d.is_dir() ]

    for d in dp:
        convert_dir(d, supported, clean, args)

################################################################################

def convert_file(in_file, clean):

    f_e = pathlib.PurePosixPath(in_file).suffix
    print(f_e)
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)

    replace = {
        "$schema": { "replaceValue": 'https://json-schema.org/draft/2020-12/schema', "add": False}
    }

    try:
        
        with open(in_file, 'r') as in_f:

            if f_e == ".json":
                i_d = in_f.read()
                s = json.loads(i_d)
                par_replace(s, replace)
                o_f = re.sub(".json", ".yaml", in_file)
                with open(o_f, 'w') as f:
                    yaml.dump(s, f)
                    print("Dumped to {}".format(o_f))
                if clean is True:
                    deleteFile(in_file)


            elif f_e == ".yaml":
                s = yaml.load( in_f )
                par_replace(s, replace)
                o_f = re.sub(".yaml", ".json", in_file)
                json.dump(s, o_f, indent = 4)
                print("Dumped to {}".format(o_f))
                if clean is True:
                    deleteFile(in_file)

    except Exception as e:
        print("Error loading the file ({}): {}".format(in_file, e) )
        exit()

################################################################################

def par_replace(schema, replace):

    for r, rv in replace.items():
        if r in schema:
            schema.update({r: rv["replaceValue"]})
        else:
            if "add" in r:
                if rv["add"] is True:
                    schema.update({r: rv["replaceValue"]})

    return schema



################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
