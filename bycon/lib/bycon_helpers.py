import base36
import humps
import inspect
import json
import random
import re
import time
import yaml

from isodate import parse_duration
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient

from config import BYC, BYC_DBS, BYC_UNCAMELED, BYC_UPPER, HTTP_HOST

################################################################################


class ByconMongo:
    def __init__(self):
        self.host_address = BYC_DBS["mongodb_host"]

    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#
    
    def openMongoDatabase(self, db_name):
        self.client = MongoClient(host=self.host_address)
        if self.__check_db_name(db_name) is False:
            return False
        self.db = self.client[db_name]
        return self.client[db_name]


    #--------------------------------------------------------------------------#

    def openMongoColl(self, db_name, coll_name="___none___"):
        self.client = MongoClient(host=self.host_address)
        if self.__check_db_name(db_name) is False:
            ByconError().addError(f"db {db_name} does not exist")
            return False
        self.db = self.client[db_name]
        if self.__check_coll_name(coll_name) is False:
            ByconError().addError(f"collection {db_name}.{coll_name} does not exist")
            return False
        return self.db[coll_name]


    #--------------------------------------------------------------------------#

    def resultList(self, db_name, coll_name, query, fields={}):
        results = []
        if (coll := self.openMongoColl(db_name, coll_name)) is not False:
            results = list(coll.find(query, fields))
        return results

    #--------------------------------------------------------------------------#
    #---------------------------- private -------------------------------------#
    #--------------------------------------------------------------------------#

    def __check_db_name(self, db_name):
        if str(db_name) not in list(self.client.list_database_names()):
            ByconError().addError(f"db `{db_name}` does not exist")
            return False
        return db_name


    #--------------------------------------------------------------------------#
    
    def __check_coll_name(self, coll_name):
        if str(coll_name) not in list(self.db.list_collection_names()):
            ByconError().addError(f"collection `{coll_name}` does not exist in `{self.db}`")
            return False
        return coll_name


################################################################################
################################################################################
################################################################################

class ByconError:
    def __init__(self):
        self.errors = BYC["ERRORS"]
        self.caller = inspect.stack()[-1].function

    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def addError(self, error=None):
        if error:
            prdbug(f"{error} - {self.caller}")
            BYC["ERRORS"].append(error)


################################################################################
################################################################################
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

    def paginated_list(self, this, skip=0, limit=300000, shuffle=False):
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

        if shuffle is True:
            random.shuffle(this)

        return this[p_range[0]:p_range[-1]]


################################################################################

def days_from_iso8601duration(iso8601duration=""):
    """A simple function to convert ISO8601 duration strings to days. This is
    potentially lossy since it does not include time zone parsing."""

    # TODO: check format
    if not re.match(r'^P\d+?[YMD](\d+?[M])?(\d+?[D])?(T[\dHMS]+?)?$', str(iso8601duration)):
        return False

    iso8601duration = iso8601duration.upper()

    d = parse_duration(iso8601duration.upper())
    days = 0
    # try catches exceptions for zero date ranges like "P0D"
    try:
        days += int(d.years) * 365.2425
        days += int(d.months) * 30.4167
        days += int(d.days)
        days += int(d.seconds) / 86400
    except Exception as e:
        return 0

    return int(days)


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
    if "___shell___" not in HTTP_HOST:
        print('Content-Type: application/json')
        print('status:200')
        print()


################################################################################

def prtexthead():
    if "___shell___" not in HTTP_HOST:
        print('Content-Type: text/plain')
        print('status: 302')
        print()


################################################################################

def prdlhead(filename="download.txt"):
    if "___shell___" not in HTTP_HOST:
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


