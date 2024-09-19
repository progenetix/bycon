import base36, humps, json, re, time

from isodate import parse_duration
from datetime import datetime
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

class RefactoredValues():

    def __init__(self, parameter_definition={}):
        self.v_list = []
        self.parameter_definition = parameter_definition

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def refVal(self, vs=[]):
        if type(vs) != list:
            vs = [vs]
        self.v_list = vs
        self.__refactor_values_from_defined_type()
        return self.v_list

    # -------------------------------------------------------------------------#
    # ----------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __refactor_values_from_defined_type(self):
        p_d_t = self.parameter_definition.get("type", "string")
        values = list(x for x in self.v_list if x is not None)
        values = list(x for x in values if x.lower() not in ["none", "null"])

        if len(values) == 0:
            self.v_list = None
            return

        defs = self.parameter_definition
        if "array" in p_d_t:
            # remapping definitions to the current item definitions
            defs = self.parameter_definition.get("items", {"type": "string"})
        p_t = defs.get("type", "string")

        v_l = []
        for v in values:
            v_l.append(self.__cast_type(defs, p_t, v))
        if "array" in p_d_t:
            self.v_list = v_l
            return

        # testing against the input values; ==0 already checked
        if len(values) == 1:
            self.v_list = v_l[0]
            return

        # re-joining for bug report ...
        self.v_list = ','.join(values)
        BYC["WARNINGS"].append(f"!!! Multiple values ({self.v_list}) for {p_d_t} in request")
        return


    # -------------------------------------------------------------------------#

    def __cast_type(self, defs, p_type, p_value):
        prdbug(f'casting {p_type} ... {p_value}')
        if "object" in p_type:
            return self.__split_string_to_object(defs, p_value)
        if "int" in p_type:
            return int(p_value)
        if "number" in p_type:
            return float(p_value)
        if "bool" in p_type:
            return test_truthy(p_value)
        return str(p_value)


    # -------------------------------------------------------------------------#

    def __split_string_to_object(self, defs, value):
        o_p = defs.get("parameters", ["id", "label"])
        o_s = defs.get("split_by", "::")
        t_s = defs.get("types", [])
        if len(t_s) != len(o_p):
            t_s = ["string"] * len(o_p)
        o = {}
        for v_i, v_v in enumerate(value.split(o_s)):
            if "int" in t_s[v_i] and re.match(r'^\d+?$', v_v):
                v_v = int(v_v)
            elif "num" in t_s[v_i] and re.match(r'^\d+?(\.\d+?)?$', v_v):
                v_v = float(v_v)
            o.update({o_p[v_i]: v_v})
        return o


################################################################################

def select_this_server() -> str:
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

    if BYC.get("PAGINATED_STATUS", False):
        return this

    BYC.update({"PAGINATED_STATUS": True})

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
        ids = list(s["id"] for s in rs)
    except Exception as e:
        BYC["ERRORS"].append(e)

    mongo_client.close()
    query = {"id": {"$in": ids}}

    return query


################################################################################

def test_truthy(this):
    if str(this).lower() in ["1", "true", "y", "yes"]:
        return True
    return False


################################################################################

def decamelize_words(j_d):
    for d in BYC_UNCAMELED:
        j_d = re.sub(r"\b{}\b".format(d), humps.decamelize(d), j_d)
    for d in BYC_UPPER:
        j_d = j_d.replace(d.lower(), d)
    return j_d


################################################################################

def prdbughead(this=""):
    BYC.update({"DEBUG_MODE": True})
    prtexthead()
    print(this)

################################################################################

def prtexthead():
    if not "local" in ENV:
        print('Content-Type: text/plain')
        print('status: 302')
        print()

################################################################################

def prdlhead(filename="download.txt"):
    if not "local" in ENV:
        print('Content-Type: text/tsv')
        print(f'Content-Disposition: attachment; filename={filename}')
        print('status: 200')
        print()


################################################################################

def prdbug(this):
    if BYC["DEBUG_MODE"] is True:
        prjsontrue(this)
        # prjsonnice(this)


################################################################################

def prjsonnice(this):
    print(decamelize_words(json.dumps(this, indent=4, sort_keys=True, default=str)) + "\n")


################################################################################

def prjsontrue(this):
    print(json.dumps(this, indent=4, sort_keys=True, default=str) + "\n")


################################################################################

def prjsoncam(this):
    prjsonnice(humps.camelize(this))


################################################################################

def isotoday():
    return str(datetime.today().strftime('%Y-%m-%d'))


################################################################################

def isonow():
    return str(datetime.datetime.now().isoformat())


################################################################################

def clean_empty_fields(this_object, protected=[]):
    if not isinstance(this_object, dict):
        return this_object
    for k in list(this_object.keys()):
        if k in protected:
            continue
        if not this_object.get(k):
            this_object.pop(k, None)
        # prdbug(f'cleaning? {k} - {this_object.get(k)}')
        elif isinstance(this_object[k], dict):
            if not this_object.get(k):
                this_object.pop(k, None)
        elif isinstance(this_object[k], list):
            if len(this_object[k]) < 1:
                this_object.pop(k, None)

    return this_object


