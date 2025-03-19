


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



from pox.core import core 
from pox.lib.util import dpid_to_str 
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import ethernet, EthAddr
from pox.lib.packet.ipv6 import IPAddr

import pox.openflow.libopenflow_01 as of

import pox.lib.packet as pkt

# use this to print stuff to the screen, there's a lot of garbage but just deal with it tbh
log = core.getLogger()

class MyComponent (object):

    serverOneMac = b"\x00\x00\x00\x00\x00\x05"
    serverTwoMac = b"\x00\x00\x00\x00\x00\x06"
    
    def __init__ (self):
        core.openflow.addListeners(self)

    def _handle_ConnectionUp (self, event):
        log.debug("Switch %s has come up.", dpid_to_str(event.dpid))
        self.connection = event.connection

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

    def doArpRequest(self, packet, a, event):
        log.debug("Specifically an ARP Packet")
        log.debug(a)
        r = arp()
        r.hwtype = a.hwtype
        r.prototype = a.prototype
        r.hwlen = a.hwlen
        r.protolen = a.protolen
        r.opcode = arp.REPLY
        r.hwdst = a.hwsrc
        r.protodst = a.protosrc
        r.protosrc = a.protodst
        r.hwsrc = EthAddr(self.serverOneMac)
            

            

        e = ethernet(type=packet.type, src=r.hwsrc,
                         dst=a.hwsrc)
        e.payload = r

        msg = of.ofp_packet_out()
        msg.data = e.pack()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
        msg.in_port = event.port
        return msg


    def _handle_PacketIn (self, event):
        log.debug("Detected a new packet!")
        packet = event.parsed
        a = packet.find('arp')
        
        
        if a:
            msg = self.doArpRequest(packet, a, event)
            # newFlow = of.ofp_flow_mod()

            newFlow = of.ofp_flow_mod()

            newFlow.idle_timeout = 2000
            newFlow.hard_timeout = 2000

            msg.buffer_id = 1

            

            newFlow.command = 0
            
            newFlow.priority = 42 # no idea why 42, it's just what the docs are saying

            newFlow.match._in_port = int(a.hwsrc.raw.hex()[-1]) # might be wrong

            newFlow.match._dl_type = 0x0800 # WHY IS THIS NOT WORKING AAAAAAAAAAAAAAAAAAA

            newFlow.match.nw_dst = IPAddr("10.0.0.10")

            newFlow.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr("10.0.0.5")))
            newFlow.actions.append(of.ofp_action_output(port = 5))

            self.connection.send(newFlow)

            event.connection.send(msg)

        else:
            log.debug("Not an ARP Packet...")
            log.debug(event.parsed)
        
# making a small change

def launch():
    core.registerNew(MyComponent)
    log.debug("Hello World inside the VM!")

