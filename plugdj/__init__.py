from .events import from_json
from .util import js_var, InvalidLogin, logger
from .base import SockBase, PlugREST, PlugSock

class PlugDJ(PlugREST):
    """ models actions and events of a single user. """

    websocket_cls = PlugSock

    def __init__(self, email, password, listener=None):
        super(PlugDJ, self).__init__()
        self.ws = self.login(email, password).acquire_socket(listener)

    def login(self, email, password):
        if super(PlugDJ, self).login(email, password).get("status") != "ok":
            raise InvalidLogin(email, password)
        return self
        # ^ socket acquisition should happen immediately after

    def acquire_socket(self, listener=None, sockopts=None):
        """ sockopts: optional knobs for WebSocket.__init__ """

        # expect next GET / to return the "Connecting..." page which will
        # contain our websocket auth token.
        connecting = super(PlugDJ, self)._get_root()
        sockopts = sockopts or {}
        return self.websocket_cls(js_var("_jm", connecting.text), listener,
                                  **sockopts)

    def set_listener(self, listener):
        self.ws.listener = listener
        return self

    def send_chat(self, msg):
        if not isinstance(msg, basestring):
            msg = str(msg)
            logger.info("Room.send_chat: converted msg into a string: " + msg)
        return self.ws.send_chat(msg)

# TODO: remove.
#
#if __name__ == "__main__":
#    import logging
#    logging.basicConfig(level=logging.DEBUG)
#    logger.info("wtf, ipython.")
