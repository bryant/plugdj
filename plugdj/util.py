from logging import getLogger

logger = getLogger(__name__)

class MalformedEvent(Exception): pass

class ServerShenanigans(Exception): pass

class InvalidLogin(Exception): pass

class LoginError(Exception): pass

def js_var(var, raw):
    """ really hacky-hack helper to extract js str var decls. """
    lestr = r"\b{0}\s*=\s*\"([^\"]+)".format(var)
    match = re.search(lestr, raw)
    return None if match is None else match.group(1)

def ms_since_epoch(dt):
    delta = (dt - datetime(1970, 1, 1))
    return int(round(delta.total_seconds() * 1000))

def expect_obj(expected, actual):
    """ handy hack that checks json dicts surjectively. """
    return {k: v for k, v in expected.iteritems() if actual.get(k) != v}
