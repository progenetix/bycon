import base36, humps, json, re, time

from isodate import parse_duration
from os import environ
from pymongo import MongoClient

from config import *

################################################################################

def set_debug_state(debug=False) -> bool:
    """
    Function to provide a text response header for debugging purposes, i.e. to 
    print out the error or test parameters to a browser session.
    The common way would be to add either a `?debugMode=true` query parameter.
    """
    if BYC["DEBUG_MODE"] is True:
        return True

    if test_truthy(debug):
        BYC.update({"DEBUG_MODE": True})
        if not "local" in ENV:
            print('Content-Type: text')
            print()
        return True

    if not "local" in ENV:
        r_uri = environ.get('REQUEST_URI', "___none___")
        if re.match(r'^.*?[?&/]debugMode?=(\w+?)\b.*?$', r_uri):
            d = re.match(r'^.*?[?&/]debugMode?=(\w+?)\b.*?$', r_uri).group(1)
            if test_truthy(d):
                print('Content-Type: text')
                print()
                BYC.update({"DEBUG_MODE": True})
                return True


################################################################################

def refactor_value_from_defined_type(parameter, values, definition):
    p_d_t = definition.get("type", "string")
    values = list(x for x in values if x is not None)
    values = list(x for x in values if x.lower() not in ["none", "null"])
    if len(values) == 0:
        return False
    if "array" in p_d_t:
        p_i_t = definition.get("items", "string")
        if "int" in p_i_t:
            return list(map(int, values))
        elif "number" in p_i_t:
            return list(map(float, values))
        else:
            return list(map(str, values))
    elif len(values) == 1:
        value = values[0]
        if "int" in p_d_t:
            return int(value)
        elif "number" in p_d_t:
            return float(value)
        elif "bool" in p_d_t:
            return test_truthy(value)
        else:
            return str(value)
    else:
        BYC["WARNINGS"].append(f"!!! Multiple values for {parameter} in request")
        # re-joining ...
        return ','.join(values)


################################################################################

def select_this_server(byc: dict) -> str:
    """
    Cloudflare based encryption may lead to "http" based server addresses in the
    URI, but then the browser ... will complain if the handover URLs won't use
    encryption. OTOH for local testing one may need to stick w/ http if no pseudo-
    https scenario had been implemented. Therefore handover addresses etc. will
    always use https _unless_ the request comes from a host listed a test instance.
    """
    s_uri = str(environ.get('SCRIPT_URI'))
    test_sites = BYC["beacon_defaults"].get("test_domains", [])
    https = "https://"
    http = "http://"

    s = f'{https}{ENV}'
    for site in test_sites:
        if site in s_uri:
            if https in s_uri:
                s = f'{https}{site}'
            else:
                s = f'{http}{site}'

    # TODO: ERROR hack for https/http mix, CORS...
    # ... since cloudflare provides https mapping using this as fallback

    return s


################################################################################

def generate_id(prefix):
    time.sleep(.001)
    return '{}-{}'.format(prefix, base36.dumps(int(time.time() * 1000)))  ## for time in ms


################################################################################

def days_from_iso8601duration(iso8601duration):
    """A simple function to convert ISO8601 duration strings to days. This is
    potentially lossy since it does not include time parsing."""

    # TODO: check format
    is_isodate_duration = re.match(r'^P\d+?[YMD](\d+?[M])?(\d+?[D])?', iso8601duration)
    if not is_isodate_duration:
        return False

    duration = parse_duration(iso8601duration)
    days = 0
    try:
        days += int(duration.years) * 365.2425
    except AttributeError:
        pass
    try:
        days += int(duration.months) * 30.4167
    except AttributeError:
        pass
    try:
        days += int(duration.days)
    except AttributeError:
        pass

    return days


################################################################################

def hex_2_rgb( hexcolor ):
    rgb = [127, 127, 127]
    h = hexcolor.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    return rgb


################################################################################

def return_paginated_list(this, skip, limit):
    if limit < 1:
        return this

    p_range = [
        skip * limit,
        skip * limit + limit,
    ]
    t_no = len(this)
    r_l_i = t_no - 1

    if p_range[0] > r_l_i:
        p_range[0] = r_l_i
    if p_range[-1] > t_no:
        p_range[-1] = t_no

    if p_range[0] > t_no:
        return []

    return this[p_range[0]:p_range[-1]]


################################################################################

def mongo_result_list(db_name, coll_name, query, fields):
    results = []

    mongo_client = MongoClient(host=DB_MONGOHOST)
    db_names = list(mongo_client.list_database_names())
    if db_name not in db_names:
        BYC["ERRORS"].append(f"db `{db_name}` does not exist")
        return results
    try:
        results = list(mongo_client[db_name][coll_name].find(query, fields))
    except Exception as e:
        BYC["ERRORS"].append(e)
    mongo_client.close()

    return results


################################################################################

def mongo_test_mode_query(db_name, coll_name, test_mode_count=5):
    query = {}
    error = False
    ids = []

    mongo_client = MongoClient(host=DB_MONGOHOST)
    db_names = list(mongo_client.list_database_names())
    if db_name not in db_names:
        BYC["ERRORS"].append(f"db `{db_name}` does not exist")
        return results, f"{db_name} db `{db_name}` does not exist"
    try:
        rs = list(mongo_client[db_name][coll_name].aggregate([{"$sample": {"size": test_mode_count}}]))
        ids = list(s["_id"] for s in rs)
    except Exception as e:
        BYC["ERRORS"].append(e)

    mongo_client.close()
    query = {"_id": {"$in": ids}}

    return query

################################################################################

def assign_nested_value(parent, dotted_key, v, parameter_definitions={}):
    parameter_type = parameter_definitions.get("type", "string")
    parameter_default = parameter_definitions.get("default")
    if v is None:
        if parameter_default:
            v = parameter_default
    if v is None:
        return parent

    if "num" in parameter_type:
        if str(v).strip().lstrip('-').replace('.','',1).isdigit():
            v = float(v)
    elif "integer" in parameter_type:
        if str(v).strip().isdigit():
            v = int(v)
    else:
        v = str(v)

    ps = dotted_key.split('.')

    if len(ps) == 1:
        if "array" in parameter_type:
            parent.update({ps[0]: v.split(',')})
        else:
            parent.update({ps[0]: v })
        return parent

    if ps[0] not in parent or parent[ ps[0] ] is None:
        parent.update({ps[0]: {}})

    if len(ps) == 2:
        if "array" in parameter_type:
            parent[ ps[0] ].update({ps[1]: v.split(',')})
        else:
            parent[ ps[0] ].update({ps[1]: v })
        return parent

    if  ps[1] not in parent[ ps[0] ] or parent[ ps[0] ][ ps[1] ] is None:
        parent[ ps[0] ].update({ps[1]: {}})
    if len(ps) == 3:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: v.split(',')})
        else:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: v })
        return parent

    if  ps[2] not in parent[ ps[0] ][ ps[1] ] or parent[ ps[0] ][ ps[1] ][ ps[2] ] is None:
        parent[ ps[0] ][ ps[1] ].update({ps[2]: {}})
    if len(ps) == 4:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v.split(',')})
        else:
            parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v })
        return parent
    
    if len(ps) > 4:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>4) !!!")
        return '_too_deep_'

    return parent

################################################################################

def get_nested_value(parent, dotted_key, parameter_type="string"):

    ps = dotted_key.split('.')

    v = ""

    if len(ps) == 1:
        try:
            v = parent[ ps[0] ]
        except:
            v = ""
    elif len(ps) == 2:
        try:
            v = parent[ ps[0] ][ ps[1] ]
        except:
            v = ""
    elif len(ps) == 3:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ]
        except:
            v = ""
    elif len(ps) == 4:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ]
        except:
            v = ""
    elif len(ps) == 5:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ][ ps[4] ]
        except:
            v = ""
    elif len(ps) > 5:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>5) !!!")
        return '_too_deep_'

    return v

################################################################################

def test_truthy(this):
    if str(this).lower() in ["1", "true", "y", "yes"]:
        return True
    return False


################################################################################

def decamelize_words(j_d):
    # TODO: move words to config
    de_cams = ["gVariants", "gVariant", "sequenceId", "relativeCopyClass", "speciesId", "chromosomeLocation", "genomicLocation"]
    for d in de_cams:
        j_d = re.sub(r"\b{}\b".format(d), humps.decamelize(d), j_d)
    return j_d


################################################################################

def prdbug(this):
    if BYC["DEBUG_MODE"] is True:
        prjsonnice(this)


################################################################################

def prjsonnice(this):
    print(decamelize_words(json.dumps(this, indent=4, sort_keys=True, default=str)) + "\n")


################################################################################

def prjsoncam(this):
    prjsonnice(humps.camelize(this))



