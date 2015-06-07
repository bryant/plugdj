from logging import getLogger
from re import search
from md5 import md5

logger = getLogger(__name__)

class MalformedEvent(Exception): pass

class ServerShenanigans(Exception): pass

class InvalidLogin(Exception):
    def __init__(self, email, pw):
        msg = "email = %s; md5(password) = %s" % (email, md5(pw).hexdigest())
        super(InvalidLogin, self).__init__(msg)

class LoginError(Exception): pass

def js_var(var, raw):
    """ really hacky-hack helper to extract js str var decls. """
    lestr = r"\b{0}\s*=\s*\"([^\"]+)".format(var)
    match = search(lestr, raw)
    return None if match is None else match.group(1)

def ms_since_epoch(dt):
    delta = (dt - datetime(1970, 1, 1))
    return int(round(delta.total_seconds() * 1000))

def expect_obj(expected, actual):
    """ handy hack that checks json dicts surjectively. """
    return {k: v for k, v in expected.iteritems() if actual.get(k) != v}
