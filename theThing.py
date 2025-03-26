'''
Made by David Turnley for cs4480 PA2

Nox Docs: https://noxrepo.github.io/pox-doc/html/#openflow-in-pox
'''

from pox.core import core 
from pox.lib.util import dpid_to_str 
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import ethernet, EthAddr
from pox.lib.packet.ipv4 import IPAddr
from typing import cast

import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class MyComponent (object):

    serverOneMac = b"\x00\x00\x00\x00\x00\x05"
    serverTwoMac = b"\x00\x00\x00\x00\x00\x06"

    serverOneIP = "10.0.0.5"
    serverTwoIP = "10.0.0.6"

    sendToOne = True

    serverOnePort = 5
    serverTwoPort = 6

    
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

    # Handles arp requests from clients and servers
    def doArpRequest(self, packet, a, event):
        log.debug("\n\nRecieved an ARP Request")
        log.debug(a)

        #Technically not needed, but helps development
        a = cast(arp, a)

        r = arp()
        r.hwtype = a.hwtype
        r.prototype = a.prototype
        r.hwlen = a.hwlen
        r.protolen = a.protolen
        r.opcode = arp.REPLY
        r.hwdst = a.hwsrc
        r.protodst = a.protosrc
        r.protosrc = a.protodst

        ethString = self.serverOneMac if self.sendToOne else self.serverTwoMac

        # Checking to see if the arp request is going to the switch, or to a client
        if a.protodst.toStr() != IPAddr("10.0.0.10").toStr():
            log.debug("Recieved non-standard arp request")
            ethString = "00:00:00:00:00:0" + str(a.protodst.toStr()[-1])
        else:
            log.debug("It's normal! Yay!")

        r.hwsrc = EthAddr(ethString)

        # Below is largely book keeping
        e = ethernet(type=packet.type, src=r.hwsrc,
                         dst=a.hwsrc)
        e.payload = r

        msg = of.ofp_packet_out()
        msg.data = e.pack()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
        msg.in_port = event.port
        return msg
    
    # Creates the needed flows to switch automatically
    def makeAndSendFlows(self, event):

        serverPort = self.serverOnePort if self.sendToOne else self.serverTwoPort
        serverIP = self.serverOneIP if self.sendToOne else self.serverTwoIP

        clientPort = event.port
        clientIP = (IPAddr("10.0.0.0" + str(clientPort)), 32) #yes this is kind of a hackey way to do it but whatever
                                                              # it is true for this assignment
        
        # Making the flow for the client towards the server
        newClientFlow = of.ofp_flow_mod()

        newClientFlow.cookie = (clientPort * 16) + serverPort # cookie appears as [clientport][serverport] ie, 15

        newClientFlow.out_port = serverPort
        newClientFlow.match._in_port = clientPort
        newClientFlow.match.dl_type = 0x0800
        newClientFlow.match.nw_dst = (IPAddr("10.0.0.10"), 32)
        newClientFlow.match.nw_src = clientIP

        newClientFlow.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr(serverIP)))
        newClientFlow.actions.append(of.ofp_action_output(port = serverPort))

        self.connection.send(newClientFlow)

        # Making the flow for the server towards the client
        newHostFlow = of.ofp_flow_mod()

        newHostFlow.cookie = (serverPort * 16) + clientPort # cookie appears as [serverport][clientport] ie, 51

        newHostFlow.out_port = clientPort
        newHostFlow.match.dl_type = 0x0800
        newHostFlow.match._in_port = serverPort
        newHostFlow.match.nw_dst = clientIP
        newHostFlow.match.nw_src = serverIP

        newHostFlow.actions.append(of.ofp_action_nw_addr.set_src(IPAddr("10.0.0.10")))
        newHostFlow.actions.append(of.ofp_action_output(port = event.port))

        self.connection.send(newHostFlow)


    def _handle_PacketIn (self, event):
        packet = event.parsed
        a = packet.find('arp')
        
        
        if a:
            if a.opcode is not arp.REQUEST:
                return
            msg = self.doArpRequest(packet, a, event) # Might as well make the arp packet right away, sends later

            a = cast(arp, a) #Technically not needed, just helps with development

            if a.protodst.toStr() == IPAddr("10.0.0.10").toStr():
                self.makeAndSendFlows(event)
                debugMessage = "5" if self.sendToOne else "6"
                log.debug("Sending client " + str(event.port) + " to: " + debugMessage)

                self.sendToOne = not self.sendToOne

            event.connection.send(msg) # Delayed sending of the arp packet to ensure that nothing is sent before the flows

            log.debug(str(self.sendToOne))

def launch():
    core.registerNew(MyComponent)
    log.debug("\n\nHello World inside the VM!\n\n")

