import csv, datetime, re, requests

from pathlib import Path
from os import environ, path
from pymongo import MongoClient
from copy import deepcopy
from random import sample as random_samples

from bycon import (
    ByconVariant,
    BYC,
    BYC_PARS,
    ENV,
    prdbug,
    prjsonnice,
    return_paginated_list
)

################################################################################

class ExportFile:

    def __init__(self, file_type=None):
        self.file_path = BYC_PARS.get("outputfile")
        self.file_type = file_type

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def checkOutputFile(self):
        if not self.file_path:
            if "___shell___" in ENV:
                BYC["ERRORS"].append("No output file specified (-o, --outputfile) => quitting ...")
            return False
        if self.file_type:
            if not self.file_path.endswith(self.file_type):
                if "___shell___" in ENV:
                    BYC["ERRORS"].append(f"The output file should be an `{self.file_type}` => quitting ...")
                return False
        return self.file_path


################################################################################


def read_tsv_to_dictlist(filepath, max_count=0):
    dictlist = []
    fieldnames = []
    with open(filepath, newline='') as csvfile:
        data = csv.DictReader(filter(lambda row: row.startswith('#') is False, csvfile), delimiter="\t", quotechar='"')
        fieldnames = list(data.fieldnames)
        for l in data:
            dictlist.append(dict(l))
    if 0 < max_count < len(dictlist):
        dictlist = random_samples(dictlist, max_count)

    return dictlist, fieldnames


################################################################################

def read_www_tsv_to_dictlist(www, max_count=0):
    dictlist = []
    fieldnames = []
    with requests.Session() as s:
        download = s.get(www)
        # TODO: error capture/return
        decoded_content = download.content.decode('utf-8')
        lines = list(decoded_content.splitlines())

        data = csv.DictReader(filter(lambda row: row.startswith('#') is False, lines), delimiter="\t", quotechar='"') # , quotechar='"'
        fieldnames = list(data.fieldnames)

        for l in data:
            dictlist.append(dict(l))

    if 0 < max_count < len(dictlist):
        dictlist = random_samples(dictlist, max_count)

    return dictlist, fieldnames


################################################################################

def callset_guess_probefile_path(callset):
    if not (local_paths := BYC.get("local_paths")):
        return False
    if not "server_callsets_dir_loc" in local_paths:
        return False
    if not "analysis_info" in callset:
        return False

    d = Path( path.join( *local_paths["server_callsets_dir_loc"]))
    n = local_paths.get("probefile_name", "___none___")

    if not d.is_dir():
        return False

    # TODO: not only geo cleaning?
    s_id = callset["analysis_info"].get("series_id", "___none___").replace("geo:", "")
    e_id = callset["analysis_info"].get("experiment_id", "___none___").replace("geo:", "")

    p_f = Path( path.join( d, s_id, e_id, n ) )

    if not p_f.is_file():
        return False

    return p_f

################################################################################

def write_log(log, log_file, ext=".log"):
    if len(log) > 0:
        print(f'=> {len(log)} log entries so there are some problems...')
        if len(ext) > 0:
            log_file += ext
        lf = open(log_file, "w")
        for ll in log:
            lf.write(f'{ll}\n')
        lf.close()
        print(f'Wrote errors to {log_file}')

