from ws4py.client.threadedclient import WebSocketClient
from .events import from_json
from .util import js_var
from .base import SockBase

class PlugSock(SockBase):
    """ default ws impl based on ws4py. spawns its own thread. """

    _recv = lambda self: self.socket.recv()
    _send = lambda self, m: self.socket.send(m)

    def __init__(self, auth, listener, **kwargs):
        class _ThreadedPlugSock(WebSocketClient):
            def opened(innerself):
                self.authenticate(self.auth)

            def received_message(innerself, msg):
                logger.debug("_ThreadedPlugSock: received %r" % m.data)
                self.listener(msg)

            def closed(innerself, code, reason=None):
                msg = "_ThreadedPlugSock: closed: %r %r" % (code, reason)
                logger.debug(msg)

        self.auth = auth
        self.listener = listener
        self.socket = _ThreadedPlugSock(self.ws_endpoint)
        self.socket.connect()

class PlugDJ(object):
    """ models actions and events of a single user. """

    websocket_cls = PlugSock

    def __init__(self, email, password, listener=None):
        self.rest = rest = PlugREST()
        self.ws = self.login(email, password).acquire_socket(listener)

    def login(self, email, password):
        if self.rest.login(email, password).get("status") != "ok":
            raise InvalidLogin
        return self
        # ^ socket acquisition should happen immediately after

    def acquire_socket(self, listener=None, sockopts=None):
        """ sockopts: optional knobs for WebSocket.__init__ """

        # expect next GET / to return the "Connecting..." page which will
        # contain our websocket auth token.
        connecting = self._get("/")
        sockopts = sockopts or {}
        return self.websocket_cls(js_var("_jm", connecting.text), listener,
                                  **sockopts)

    def join_room(self, room, handler):
        self.rest.join_room(room)
        req = self.rest.join_room(room)
        # TODO: handle invalid room
        logger.debug("Room: join_room returned " + req)
        return Room(room, self.rest, self.ws)

    # TODO: copy appropriate PlugREST calls into class namespace

class Room(object):
    """ room state. NOTE: invalidated upon next call to PlugDJ.join_room. """

    def __init__(self, room, rest, ws):
        """ instances should be obtained from PlugDJ.join_room. """

        self.rest = rest
        self.ws = ws

    def chat_delete(self, msgid):
        return self._delete(urljoin("/_/chat", msgid))

    def moderate_skip(self):
        # TODO: decide whether to track room state
        s = self.rest.room_state()["data"][0]
        return self.rest.moderate_skip(s["booth"]["currentDJ"],
                                       s["playback"]["historyID"])

    def send_chat(self, msg):
        if not isinstance(msg, basestring):
            logger.info("Room.send_chat: converted msg %r into a string" % msg)
            msg = str(msg)
        return self.ws.send_chat(msg)

# TODO: remove.
#
#if __name__ == "__main__":
#    import logging
#    logging.basicConfig(level=logging.DEBUG)
#    logger.info("wtf, ipython.")
