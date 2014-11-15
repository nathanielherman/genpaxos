#!/usr/bin/python
import os
import sys
import time
import threading

import multiconsensus
import fakenetwork
import logprogstate
import eventhandler
import appstate
import Queue

N = 3

def initialize(consensus):
    consensus.proseq = 0
    consensus.isSeq = consensus.proseq == consensus.cert

class SlottedValue(object):
    def __init__(self, slot, cmd):
        self.slot = slot
        self.cmd = cmd
    def __repr__(self):
        return repr((self.slot, self.cmd))

def main():
    replicas = []
    for i in xrange(N):
        cert_chan = Queue.Queue()
        snap_chan = Queue.Queue()
        progstate = logprogstate.LogProgstate(appstate.LogDB())
        consensus = multiconsensus.MultiConsensus(i, progstate, 
                                                  1, N, cert_chan, snap_chan)
        initialize(consensus)
        handler = eventhandler.EventHandler(consensus, None, cert_chan, snap_chan)
        net = fakenetwork.FakeNetwork(None, handler)
        handler.network = net

        replicas.append(net)

    for r in replicas:
        r.config = replicas

    replicas[0].me.client_request(SlottedValue(0, appstate.Cmd("foo")))
    replicas[0].me.client_request(SlottedValue(1, appstate.Cmd("bar")))

if __name__ == '__main__':
    try:
        main()
        raw_input()
    finally:
        pass
#        os._exit(0)
