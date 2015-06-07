from plugdj.events import from_json, Chat
import json
import logging

logger = logging.getLogger(__name__)

class Echo(object):
    def __call__(self, event):
        e = from_json(event)
        logger.debug("got an event, it was %r" % e)
        try:
            if "@chefjohn" in e.message:
                self.plug.send_chat("i wuv u too, @%s" % e.un)
        except AttributeError:
            pass

    def __init__(self, plug):
        self.plug = plug
        plug.set_listener(self)
        plug.join_room("bzcuit")

if __name__ == "__main__":
    from plugdj import PlugDJ
    from plugdj.tests import creds
    from time import sleep

    logging.basicConfig(level=logging.DEBUG)

    p = Echo(PlugDJ(creds.email, creds.password))

    while True:
        sleep(2000)
