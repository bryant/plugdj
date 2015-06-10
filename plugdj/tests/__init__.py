from plugdj import PlugDJ
from plugdj.util import InvalidLogin
from nose import tools
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

def test_send_nonstring_chat():
    assert is_ok(p.join_room(creds.room))
    p.send_chat(25)

def test_really_long_chat():
    assert is_ok(p.join_room(creds.room))
    p.send_chat("hello world!" * 256)

def test_user_info():
    assert is_ok(p.user_info())

@tools.raises(InvalidLogin)
def test_fail_login():
    PlugDJ("bogus", "reallybogus")

def test_get_room_state():
    assert is_ok(p.join_room(creds.room))
    assert is_ok(p.room_state())

# cached instance for tests that don't require a fresh one
p = None
def setup_module():
    global p
    p = get_plug()
