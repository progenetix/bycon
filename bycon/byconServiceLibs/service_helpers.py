import re, time, base36
from humps import decamelize
from os import path
from pathlib import Path

from bycon import load_yaml_empty_fallback, BYC, BYC_PARS, ENV, prdbug, prtexthead

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

def assert_single_dataset_or_exit():
    if len(BYC["BYC_DATASET_IDS"]) == 1:
        return BYC["BYC_DATASET_IDS"][0]
    prtexthead()
    print("No single existing dataset was provided with -d or --datsetIds: Please reconsider.")
    exit()




