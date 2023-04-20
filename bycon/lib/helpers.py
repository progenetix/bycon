import time, base36

################################################################################

def generate_id(prefix):

    time.sleep(.001)
    return '{}-{}'.format(prefix, base36.dumps(int(time.time() * 1000))) ## for time in ms

