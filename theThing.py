


'''
Okay so from what I've learned so far, the "core" just does a lot of general stuff

here's where a lot of the important info is: https://noxrepo.github.io/pox-doc/html/#openflow-in-pox

it is pain

_handle_[eventName] is the method name for a specific event handler

message stuff is here: https://noxrepo.github.io/pox-doc/html/#openflow-messages

ofp_flow_mod is is the way to add/modify a rule in the switch

information on the actions that can be taken from a rule are here: https://noxrepo.github.io/pox-doc/html/#openflow-actions

Good luck and I bid you well

'''



from pox.core import core # type: ignore
from pox.lib.util import dpid_to_str # type: ignore

# use this to print stuff to the screen, there's a lot of garbage but just deal with it tbh
log = core.getLogger()

class MyComponent (object):
    def __init__ (self):
        core.openflow.addListeners(self)

    def _handle_ConnectionUp (self, event):
        log.debug("Switch %s has come up.", dpid_to_str(event.dpid))

    def _handle_PortStatus (self, event):
        if event.added :
            # port was added to the switch
            log.debug("Added port: $s", event.port)

        if event.deleted:
            # port was removed from the switch
            log.debug("Removed port: $s", event.port)

        if not event.added and not event.deleted:
            #port was modified
            log.debug("Modified port: %s", event.port)

    def _handle_PacketIn (self, event):
        log.debug("Detected a new packet!")
        log.debug(bytes(event.data).decode())


def launch():
    core.registerNew(MyComponent)
    log.debug("Hello World inside the VM!")
