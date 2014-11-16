#!/usr/bin/python
import os
import sys
import time
import threading

import multiconsensus
import fakenetwork
import fakenetworkdebug
import logprogstate
from logprogstate import SlottedValue
import eventhandler
import appstate
import Queue

N = 3
START_MASTER = -1

def initialize(consensus):
    if START_MASTER != -1:
        consensus.proseq = START_MASTER
        consensus.isSeq = consensus.proseq == consensus.cert

def test_mismatchedlogs(replicas):
    replicas[0].me.timeout()
    replicas[1].crashed = True
    replicas[2].crashed = True
    replicas[0].me.client_request(SlottedValue(0, appstate.Cmd("bar")))
    replicas[0].crashed = True
    replicas[1].me.timeout()

def test_recovery(replicas):
    replicas[0].me.timeout()
    replicas[0].me.client_request(SlottedValue(0, appstate.Cmd("bar")))
    replicas[1].crashed = True
    replicas[0].me.client_request(SlottedValue(1, appstate.Cmd("foo")))
    replicas[1].crashed = False
    replicas[0].me.client_request(SlottedValue(2, appstate.Cmd("baz")))
    replicas[2].crashed = True
    replicas[0].me.timeout()
    replicas[0].me.client_request(SlottedValue(3, appstate.Cmd("fuzz")))

def main():
    replicas = []
    for i in xrange(N):
        cert_chan = Queue.Queue()
        snap_chan = Queue.Queue()
        progstate = logprogstate.LogProgstate(appstate.LogDB())
        consensus = multiconsensus.MultiConsensus(i, progstate, 
                                                  1 if START_MASTER else 0, N, cert_chan, snap_chan)
        initialize(consensus)
        handler = eventhandler.EventHandler(consensus, None, cert_chan, snap_chan)
        net = fakenetworkdebug.FakeNetworkDebug(None, handler)
        handler.network = net

        replicas.append(net)

    for r in replicas:
        r.config = replicas


    replicas[0].me.timeout()
    replicas[0].me.client_request(SlottedValue(0, appstate.Cmd("bar")))
    replicas[0].crashed = True

    replicas[1].me.timeout()
    replicas[1].me.client_request(SlottedValue(1, appstate.Cmd("foo")))
    replicas[1].me.client_request(SlottedValue(2, appstate.Cmd("baz")))

    for r in replicas:
        print r.me.consensus.progstate
#    replicas[2].me.timeout()



if __name__ == '__main__':
    try:
        main()
        raw_input()
    finally:
        pass
#        os._exit(0)
