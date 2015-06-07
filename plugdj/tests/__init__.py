from plugdj import PlugDJ
from . import _creds as creds

def get_plug(listener=None):
    return PlugDJ(creds.email, creds.password, listener)

def test_login():
    p = get_plug()

#def test_join_room():
#    p = get_plug()
#    p.join_room(creds.room)
