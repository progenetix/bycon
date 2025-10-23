import base36, humps, json, re, time, yaml

from isodate import parse_duration
from datetime import datetime
from os import environ
from pathlib import Path
from pymongo import MongoClient

from config import *

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

class ByconH:
    def __init__(self):
        self.env = HTTP_HOST

    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def truth(self, this):
        if str(this).lower() in ["1", "true", "y", "yes"]:
            return True
        return False

    #--------------------------------------------------------------------------#

    def paginated_list(self, this, skip=0, limit=300000):
        if limit < 1:
            return list(this)
        if len(list(this)) < 1:
            return []

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

def select_this_server() -> str:
    """
    Cloudflare based encryption may lead to "http" based server addresses in the
    URI, but then the browser ... will complain if the handover URLs won't use
    encryption. OTOH for local testing one may need to stick w/ http if no pseudo-
    https scenario had been implemented. Therefore handover addresses etc. will
    always use https _unless_ the request comes from a host listed as test instance.
    """
    s_uri = str(environ.get('SCRIPT_URI'))
    X_FORWARDED_PROTO = str(environ.get('HTTP_X_FORWARDED_PROTO'))

    test_sites = BYC.get("test_domains", [])

    # for k in environ.keys():
    #     prdbug(f'{k} => {str(environ.get(k))}')

    s = f'https://{HTTP_HOST}'
    if not "https" in s_uri and not "https" in X_FORWARDED_PROTO:
        s = s.replace("https://", "http://")

    return s


################################################################################

def days_from_iso8601duration(iso8601duration=""):
    """A simple function to convert ISO8601 duration strings to days. This is
    potentially lossy since it does not include time parsing."""

    # TODO: check format
    # is_isodate_duration = is_isodate_duration.upper()
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
    # try:
    #     days += int(duration.seconds) / 
    # except AttributeError:
    #     pass

    return int(days)


################################################################################

def mongo_result_list(db_name, coll_name, query, fields={}):
    results = []

    mongo_client = MongoClient(host=BYC_DBS["mongodb_host"])
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

def dict_replace_values(this_dict, old_value, new_value):
    for k, v in this_dict.items():
        if type(v) is dict:
            this_dict[k] = dict_replace_values(v, old_value, new_value)
        elif type(v) is list:
            new_list = []
            for i in v:
                if type(i) is dict:
                    new_list.append(dict_replace_values(i, old_value, new_value))
                elif type(i) is str and old_value in i:
                    new_list.append(i.replace(old_value, new_value))
                else:
                    new_list.append(i)
            this_dict[k] = new_list
        elif type(v) is str and old_value in v:
            this_dict[k] = v.replace(old_value, new_value)
    return this_dict


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

def prjsonhead():
    if not "___shell___" in HTTP_HOST:
        print('Content-Type: application/json')
        print('status:200')
        print()


################################################################################

def prtexthead():
    if not "___shell___" in HTTP_HOST:
        print('Content-Type: text/plain')
        print('status: 302')
        print()


################################################################################

def prdlhead(filename="download.txt"):
    if not "___shell___" in HTTP_HOST:
        print('Content-Type: text/tsv')
        print(f'Content-Disposition: attachment; filename={filename}')
        print('status: 200')
        print()


################################################################################

def prdbug(this):
    if BYC["DEBUG_MODE"] is True:
        prjsontrue(this)


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
    return str(datetime.now().isoformat())


################################################################################

def clean_empty_fields(this_object, protected=["external_references"]):
    if not isinstance(this_object, dict):
        return this_object
    for k in list(this_object.keys()):
        if k in protected:
            continue
        if not this_object.get(k):
            this_object.pop(k, None)
        elif isinstance(this_object[k], dict):
            if not this_object.get(k):
                this_object.pop(k, None)
        elif isinstance(this_object[k], list):
            if len(this_object[k]) < 1:
                this_object.pop(k, None)

    return this_object


################################################################################

def load_yaml_empty_fallback(yp):
    y = {}
    f = Path(yp)
    if not f.is_file():
        return y
    with open( yp ) as yd:
        y = yaml.load( yd , Loader=yaml.FullLoader)
    return y
    

################################################################################

def get_nested_value(parent, dotted_key, parameter_type="string"):
    ps = str(dotted_key).split('.')
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


