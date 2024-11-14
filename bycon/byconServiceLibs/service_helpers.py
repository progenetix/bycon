import re, time, base36, datetime
from humps import decamelize
from os import path
from pathlib import Path

from bycon import load_yaml_empty_fallback, BYC, BYC_PARS, ENV, prdbug, prtexthead

################################################################################

class ByconID:
    def __init__(self, sleep=0.01):
        self.errors = []
        self.prefix = ""
        self.sleep = sleep


    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def makeID(self, prefix=""):
        time.sleep(self.sleep)
        linker = "-" if len(str(prefix)) > 0 else ""
        return f'{prefix}{linker}{base36.dumps(int(time.time() * 1000))}'


################################################################################

def ask_limit_reset():
    limit = BYC_PARS.get("limit")
    if limit > 0 and limit < 1000: 
        proceed = input(f'Do you want to really want to process max. `--limit {limit}` items?\n(Y, n or enter number; use 0 for no limit): ')
        if "n" in proceed.lower():
            exit()
        elif re.match(r'^\d+?$', proceed):
            BYC_PARS.update({"limit": int(proceed)})
            if int(proceed) == 0:
                proceed = "∞"
            print(f'... now using {proceed} items')


################################################################################

def read_service_prefs(service, service_pref_path):
    # snake_case paths; e.g. `intervalFrequencies` => `interval_frequencies.yaml`
    service = decamelize(service)
    f = Path( path.join( service_pref_path, service+".yaml" ) )
    if f.is_file():
        BYC.update({"service_config": load_yaml_empty_fallback( f ) })

    if (sdefs := BYC["service_config"].get("defaults")):
        for k, v in sdefs.items():
            BYC.update({k: v})


################################################################################

def open_text_streaming(filename="data.pgxseg"):
    if not "___shell___" in ENV:
        print('Content-Type: text/plain')
        if not "browser" in filename:
            print('Content-Disposition: attachment; filename="{}"'.format(filename))
        print('status: 200')
        print()


################################################################################

def close_text_streaming():
    print()
    prdbug(f'... closing text streaming at {datetime.datetime.now().strftime("%H:%M:%S")}')
    exit()


################################################################################

def open_json_streaming(filename="data.json"):
    meta = BYC["service_response"].get("meta", {})

    if not "___shell___" in ENV:
        print_json_download_header(filename)

    print('{"meta":', end='')
    print(json.dumps(camelize(meta), indent=None, sort_keys=True, default=str), end=",")
    print('"response":{', end='')
    for r_k, r_v in BYC["service_response"].items():
        if "results" in r_k:
            continue
        if "meta" in r_k:
            continue
        print('"' + r_k + '":', end='')
        print(json.dumps(camelize(r_v), indent=None, sort_keys=True, default=str), end=",")
    print('"results":[', end="")


################################################################################

def print_json_download_header(filename):
    print('Content-Type: application/json')
    print(f'Content-Disposition: attachment; filename="{filename}"')
    print('status: 200')
    print()


################################################################################

def close_json_streaming():
    print(']}}')
    exit()


################################################################################

def generate_id(prefix=""):
    time.sleep(.001)
    return f'{prefix}{"-" if len(str(prefix)) > 0 else ""}{base36.dumps(int(time.time() * 1000))}'



################################################################################

def assertSingleDatasetOrExit():
    if len(BYC["BYC_DATASET_IDS"]) == 1:
        return BYC["BYC_DATASET_IDS"][0]
    prtexthead()
    print("No single existing dataset was provided with -d or --datsetIds: Please reconsider.")
    exit()




