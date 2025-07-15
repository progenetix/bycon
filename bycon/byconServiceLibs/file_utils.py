import csv, re, requests

from pathlib import Path
from os import environ, pardir, path
from pymongo import MongoClient
from random import sample as random_samples

from bycon import (
    ByconVariant,
    BYC,
    BYC_PARS,
    ENV,
    PROJECT_PATH,
    prdbug,
    prjsonnice,
    return_paginated_list
)


################################################################################

class ExportFile:
    def __init__(self, file_type=None):
        self.file_path = BYC_PARS.get("outputfile", False)
        self.file_type = file_type

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def check_outputfile_path(self):
        if not self.file_path:
            e = "No output file specified (-o, --outputfile) => quitting ..."
            self.__handle_file_error(e)
        if self.file_path and type(self.file_type) is str:
            if not self.file_path.endswith(str(self.file_type)):
                e = f"The output file should be an `{self.file_type}` => quitting ..."
                self.__handle_file_error(e)
        if not self.file_path:
            return False
        file_dir, file_name = path.split(path.abspath(self.file_path))
        if not path.isdir(file_dir):
            e = f"The output directory\n    {file_dir}\ndoes not exist => quitting ..."
            self.__handle_file_error(e)
        return self.file_path


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __handle_file_error(self, error=None):
        if not error:
            return
        if "___shell___" in ENV:
            print(error)
            exit()
        BYC["ERRORS"].append(error)
        self.file_path = False


################################################################################

class ByconTSVreader():
    def __init__(self):
        self.dictlist = []
        self.fieldnames = []
        self.tsv_data = None
        self.max_lines = 0


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def file_to_dictlist(self, filepath, max_count=None):
        if type(max_count) is int:
            self.max_lines = max_count
        with open(filepath, newline='') as self.tsv_data:
            self.__dictread()
        return self.dictlist, self.fieldnames


    # -------------------------------------------------------------------------#

    def www_to_dictlist(self, www, max_count=None):
        if type(max_count) is int:
            self.max_lines = max_count
        with requests.Session() as s:
            download = s.get(www)
            # TODO: error capture/return
            decoded_content = download.content.decode('utf-8')
            self.tsv_data = list(decoded_content.splitlines())
            self.__dictread()
        return self.dictlist, self.fieldnames


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __dictread(self):
        data = csv.DictReader(filter(lambda row: row.startswith('#') is False, self.tsv_data), delimiter="\t", quotechar='"')
        self.fieldnames = list(data.fieldnames)
        for l in data:
            self.dictlist.append(dict(l))
        if 0 < self.max_lines < len(self.dictlist):
            self.dictlist = random_samples(self.dictlist, self.max_lines)


################################################################################
################################################################################
################################################################################

def log_path_root():
    logdir_parts = map(lambda x: eval(x.replace("___", "")) if "___" in x else x, BYC["env_paths"]["housekeeping_log_dir_loc"])
    return path.join(*logdir_parts)

################################################################################

def write_log(log, log_file, ext=".log"):
    if len(log) > 0:
        print(f'=> {len(log)} log entries ...')
        if len(ext) > 0:
            log_file += ext
        lf = open(log_file, "w")
        for ll in log:
            lf.write(f'{ll}\n')
        lf.close()
        print(f'Wrote log to {log_file}')

