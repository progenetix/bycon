import base36
import time
import re
from isodate import parse_duration

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


