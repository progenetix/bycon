import base36
import time
import re
from isodate import parse_duration
from os import environ
from pymongo import MongoClient

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
    error = False

    mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    db_names = list(mongo_client.list_database_names())
    if db_name not in db_names:
        return results, f"{db_name} db `{db_name}` does not exist"

    try:
        results = list(mongo_client[db_name][coll_name].find(query, fields))
    except Exception as e:
        error = e

    mongo_client.close()

    return results, error


################################################################################

def mongo_test_mode_query(db_name, coll_name, test_mode_count=5):
    
    query = {}
    error = False
    ids = []

    mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    db_names = list(mongo_client.list_database_names())
    if db_name not in db_names:
        return results, f"{db_name} db `{db_name}` does not exist"
    try:
        rs = list(mongo_client[db_name][coll_name].aggregate([{"$sample": {"size": test_mode_count}}]))
        ids = list(s["_id"] for s in rs)
    except Exception as e:
        error = e

    mongo_client.close()
    query = {"_id": {"$in": ids}}

    return query, error

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

