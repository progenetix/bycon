import csv
import re

from pathlib import Path
from os import environ, path
from pymongo import MongoClient
from random import sample as random_samples

from bycon import (
    ByconVariant,
    BYC,
    BYC_PARS,
    HTTP_HOST,
    PROJECT_PATH,
    ByconError,
    prdbug,
    prjsonnice
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
        if "___shell___" in HTTP_HOST:
            print(error)
            exit()
        ByconError().addError(error)
        self.file_path = False


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

