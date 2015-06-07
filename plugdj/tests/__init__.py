from plugdj import PlugDJ
from . import _creds as creds

def get_plug(listener=None):
    return PlugDJ(creds.email, creds.password, listener)

def is_ok(json):
    return json["status"] == "ok"

def test_join_room():
    assert is_ok(p.join_room(creds.room))

def test_chat():
    assert is_ok(p.join_room(creds.room))
    p.send_chat("hello world!")

def test_really_long_chat():
    assert is_ok(p.join_room(creds.room))
    p.send_chat("hello world!" * 256)

plug = get_plug()
