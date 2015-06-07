from urlparse import urljoin
from requests import Session
from ws4py.client.threadedclient import WebSocketClient
from .util import js_var, logger, ms_since_epoch, LoginError
import json

class PlugREST(object):
    #justrestthings

    rest_url_base = "https://plug.dj"

    def __init__(self):
        self._session = Session()
        # TODO: appropriate ua
        self._session.headers.update({"User-Agent": "plugAPI_3.2.1"})

    def _post(self, path, return_req=False, **kwargs):
        req = self._session.post(self.to_url(path), **kwargs)
        if return_req:
            return req
        return req.json()

    def _get(self, path, return_req=False, **kwargs):
        req = self._session.get(self.to_url(path), **kwargs)
        if return_req:
            return req
        return req.json()

    def _get_root(self):
        return self._session.get(urljoin(self.rest_url_base, "/"))

    @classmethod
    def to_url(cls, endpoint):
        return urljoin(cls.rest_url_base, "/_/" + endpoint)

    def login(self, email, password):
        # request root of site
        csrf = js_var("_csrf", self._get_root().text)
        if csrf is None:
            raise LoginError(resp)

        json = {"csrf": csrf, "email": email, "password": password}
        return self._post("auth/login", json=json)

    # many of these have implicit preconditions. not really REST.

    def join_room(self, room):
        return self._post("rooms/join", json={"slug": room})

    def user_info(self):
        return self._get("users/me")

    def moderate_skip(self, user_id, history_id):
        json={"userID": user_id, "historyID": history_id}
        return self._post("booth/skip", json=json)

    def room_state(self):
        """ assumes already connected to room."""
        return self._get("rooms/state")

    def chat_delete(self):
        raise NotImplemented("chat/")

    def history(self):
        raise NotImplemented("rooms/history")

    def moderate_add_dj(self):
        raise NotImplemented("booth/add")

    def moderate_ban(self):
        raise NotImplemented("bans/add")

    def moderate_booth(self):
        raise NotImplemented("booth")

    def moderate_move_dj(self):
        raise NotImplemented("booth/move")

    def moderate_mute(self):
        raise NotImplemented("mutes")

    def moderate_permissions(self):
        raise NotImplemented("staff/update")

    def moderate_remove_dj(self):
        raise NotImplemented("booth/remove/")

    def moderate_staff(self):
        raise NotImplemented("staff/")

    def moderate_unban(self):
        raise NotImplemented("bans/")

    def moderate_unmute(self):
        raise NotImplemented("mutes/")

    def playlist(self):
        raise NotImplemented("playlists")

    def room_cycle_booth(self):
        raise NotImplemented("booth/cycle")

    def room_info(self):
        raise NotImplemented("rooms/update")

    def room_lock_booth(self):
        raise NotImplemented("booth/lock")

    def user_get_avatars(self):
        raise NotImplemented("store/inventory/avatars")

    def user_set_avatar(self):
        raise NotImplemented("users/avatar")

    def user_set_status(self):
        raise NotImplemented("users/status")

class SockBase(object):
    """ whose primary purpose is to receive pushes and send chats. """

    ws_endpoint = "wss://godj.plug.dj:443/socket"

    def _recv(self): raise NotImplemented

    def _send(self, m): raise NotImplemented

    def authenticate(self, tok):
        """ sends auth token. """
        logger.debug("PlugSock: sending auth.")
        self.send("auth", tok)
        return self

    def send_chat(self, msg):
        if len(msg):
            logger.warn("Room.send_chat: msg len > 256; plug will likely "
                        "truncate.")
        return self.send("chat", msg)

    def send(self, event_type, event_data):
        """ sends generic json packed in plug's format. """
        msg = self.pack_msg(event_type, event_data)
        self._send(json.dumps(msg))
        return self

    def recv(self):
        return (from_json(e) for e in json.loads(self._recv()))

    def recv_all(self):
        return list(self.recv())

    def pack_msg(self, ty, dat):
        return {"a": ty, "p": dat, "t": ms_since_epoch()}

class PlugSock(SockBase):
    """ default ws impl based on ws4py. spawns its own thread. """

    _recv = lambda self: self.socket.recv()
    _send = lambda self, m: self.socket.send(m)

    def __init__(self, auth, listener, **kwargs):
        class _ThreadedPlugSock(WebSocketClient):
            def opened(innerself):
                self.authenticate(self.auth)

            def received_message(innerself, msg):
                logger.debug("_ThreadedPlugSock: received %r" % msg.data)
                self.listener(msg)

            def closed(innerself, code, reason=None):
                msg = "_ThreadedPlugSock: closed: %r %r" % (code, reason)
                logger.debug(msg)

        self.auth = auth
        self.listener = listener or (lambda n: n)
        self.socket = _ThreadedPlugSock(self.ws_endpoint)
        self.socket.connect()
