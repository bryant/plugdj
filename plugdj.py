#from plugdj.urlopener import UrlOpener
from urlparse import urljoin
from requests import Session
from ws4py.client.threadedclient import WebSocketClient
from websocket import WebSocket
from datetime import datetime
from logging import getLogger
import re
import json

class DetailedException(Exception):
    def __init__(self, msg): self.msg = msg
    def __str__(self): return repr(self.msg)

class ServerShenanigans(DetailedException): pass

class InvalidLogin(Exception): pass

class LoginError(DetailedException): pass

def js_var(var, raw):
    """ really hacky-hack helper to extract js str var decls. """
    lestr = r"\b{0}\s*=\s*\"([^\"]+)".format(var)
    match = re.search(lestr, raw)
    return None if match is None else match.group(1)

def ms_since_epoch(dt):
    delta = (dt - datetime(1970, 1, 1))
    return int(round(delta.total_seconds() * 1000))

class LoggerMixin(object):
    logger = getLogger(__name__)

class PlugDJ(LoggerMixin):
    BASE = "https://plug.dj"
    LOGIN = "/_/auth/login"

    def __init__(self, email, password, sockopts=None):
        self._session = Session()
        self._session.headers.update({"User-Agent": "plugAPI_3.2.1"})
        self.websocket = self._login(email, password, sockopts)

    def _login(self, email, password, sockopts=None):
        csrf = js_var("_csrf", self._get("/").text)
        if csrf is None:
            raise LoginError(resp)

        json = {"csrf": csrf, "email": email, "password": password}
        req = self._post(self.LOGIN, json=json).json()
        if req.get("status") != "ok":
            raise InvalidLogin

        return self._open_push_chan(sockopts)

    def _open_push_chan(self, sockopts=None):
        """ sockopts: optional knobs for WebSocket.__init__ """

        # expect next GET / to return the "Connecting..." page which will
        # contain our websocket auth token.
        connecting = self._get("/")
        sockopts = sockopts or {}
        # TODO: remove
        svtime = datetime.strptime(js_var("_st", connecting.text),
                                   "%Y-%m-%d %H:%M:%S.%f")
        return PlugSock2(js_var("_jm", connecting.text), **sockopts)

    def _post(self, path, **kwargs):
        return self._session.post(urljoin(self.BASE, path), **kwargs)

    def _get(self, path, **kwargs):
        return self._session.get(urljoin(self.BASE, path), **kwargs)

    def join_room(self, room):
        return Room(room, self)

class Room(LoggerMixin):
    """ room state. NOTE: invalidated upon next call to PlugDJ.join_room. """

    def chat_delete(self, msgid):
        return self._delete(urljoin("/_/chat", msgid))

    def moderate_skip(self):
        pass

    def send_chat(self, msg):
        if not isinstance(msg, basestring):
            self.logger.info("Room.send_chat: converted msg %r into a string" %
                             msg)
            msg = str(msg)
        if len(msg):
            self.logger.info("Room.send_chat: msg is longer than 256 or "
                             "whatever.")
        return self.websocket.send_chat(msg)

    def user_info(self):
        return self._get("/_/users/me")

    # amounts to stateful REST, tsk.
    PER_ROOM_ENDPOINTS = {
        "chat_delete": "/chat/",
        "history": "/rooms/history",
        "moderate_add_dj": "/booth/add",
        "moderate_ban": "/bans/add",
        "moderate_booth": "/booth",
        "moderate_move_dj": "/booth/move",
        "moderate_mute": "/mutes",
        "moderate_permissions": "/staff/update",
        "moderate_remove_dj": "/booth/remove/",
        "moderate_skip": "/booth/skip",
        "moderate_staff": "/staff/",
        "moderate_unban": "/bans/",
        "moderate_unmute": "/mutes/",
        "playlist": "/playlists",
        "room_cycle_booth": "/booth/cycle",
        "room_info": "/rooms/update",
        "room_lock_booth": "/booth/lock",
        "user_info": "/users/me",
        "user_get_avatars": "/store/inventory/avatars",
        "user_set_avatar": "/users/avatar",
        "user_set_status": "/users/status",
    }

    _post = lambda self, *args, **kwargs: self.plugobj._post(*args, **kwargs)
    _get = lambda self, *args, **kwargs: self.plugobj._get(*args, **kwargs)
    _delete = lambda self, *args, **kwargs: self.plugobj._delete(*args, **kwargs)

    def __init__(self, room, plugobj):
        """ instances should be obtained from PlugDJ.join_room. """

        # could possibly cause ref cycle in future. consider weakref.
        self.plugobj = plugobj
        self.websocket = plugobj.websocket

        self.logger.debug("Room: user_info returned %r" % self.user_info().text)
        req = self._post("/_/rooms/join", json={"slug": room})
        self.logger.debug("Room: join_room returned " + req.text)

class PlugSock(LoggerMixin):
    """ whose primary purpose is to receive pushes and send chats. """

    PLUG_WS_ENDPOINT = "wss://godj.plug.dj:443/socket"

    def __init__(self, auth):
        s = self.socket = WebSocket()

        # connect and auth
        s.connect(self.PLUG_WS_ENDPOINT)
        self.authenticate(auth)

        self.auth = auth  # TODO: don't store if unnecessary

    def authenticate(self, tok):
        self.logger.debug("PlugSock: sending auth.")
        self.psend("auth", tok)
        self.expect_reply({"a": "ack", "p": "1"})
        self.logger.debug("PlugSock: auth went well.")
        return self

    def send_chat(self, msg):
        # TODO: investigate length limits
        return self.psend("chat", msg)

    def psend(self, event_type, event_data):
        """ sends generic json packed in plug's format. """
        msg = self.pack_msg(event_type, event_data)
        self.socket.send(json.dumps(msg))
        return self

    def precv(self):
        reply = json.loads(self.socket.recv())
        self.logger.debug("PlugSock: reply had length " + str(len(reply)))
        return reply[0]

    def expect_reply(self, checks):
        reply = self.precv()
        for k, v in checks.iteritems():
            if reply.get(k) != v:
                raise ServerShenanigans("Unmatched key %r in: %r" % (k, reply))

    def pack_msg(self, ty, dat):
        return {"a": ty, "p": dat, "t": ms_since_epoch(datetime.now())}

# TODO: remove
class PlugSock2(PlugSock):
    def __init__(self, auth):
        self.auth = auth
        s = self.socket = WebSocketClient(self.PLUG_WS_ENDPOINT)
        for attr in ("opened", "received_message", "closed"):
            setattr(self.socket, attr, getattr(self, attr))
        s.connect()

    def opened(self):
        self.authenticate(self.auth)

    def authenticate(self, tok):
        self.logger.debug("PlugSock2: sending auth, skipping reply check.")
        self.psend("auth", tok)

    def received_message(self, m):
        self.logger.debug("PlugSock2: received %r" % m.data)

    def closed(self, code, reason=None):
        self.logger.debug("PlugSock2: closed: %r %r" % (code, reason))

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    print "wtf, ipython."
