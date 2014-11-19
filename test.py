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

def go(f):
    #f()
    threading.Thread(target=f).start()

def test_recovery(replicas):
    '''Tests whether replicas with out of date state can keep participating successfully

    Expected outcome:
    fuzz gets successfully committed (but will only be in 0's appstate)
    1 has fuzz in the log but not committed
    2 has everything before fuzz in log (because it crashes then)'''
    replicas[0].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("bar"))
    replicas[1].crashed = True
    replicas[0].me.client_request(appstate.Cmd("foo"))
    replicas[1].crashed = False
    replicas[0].me.client_request(appstate.Cmd("baz"))
    replicas[2].crashed = True
    replicas[0].me.client_request(appstate.Cmd("fuzz"))

    #replicas[1].me.timeout()
    for r in replicas:
        print r.me.consensus.progstate

def test_mismatchedlogs(replicas):
    '''Tests whether recovery works in the case where different replicas disagree on logs

    Expected outcome:
    everyone puts bar2 in their appstate, bar gets obliterated
    (replica 1 will have an out of date rid for it)'''
    replicas[0].me.timeout()
    replicas[1].crashed = True
    replicas[2].crashed = True
    go(lambda: replicas[0].me.client_request(appstate.Cmd("bar")))
    time.sleep(.5)
    replicas[0].crashed = True
    replicas[1].crashed = False
    replicas[2].crashed = False
    replicas[1].me.timeout()
    replicas[1].me.client_request(appstate.Cmd("bar2"))
    replicas[1].crashed = True
    replicas[0].crashed = False
    replicas[0].me.timeout()
    replicas[0].me.timeout()
    for r in replicas:
        print r.me.consensus.progstate

def test_gap(replicas):
    '''Tests whether gaps in the log successfully get filled with NOPs

    Expected outcome:
    slot 1 gets replaced with a NOP, giving final appstate
    ['bar','baz','fuzz'] for 1 and 2, but just 'bar' for 0 (who crashes)
    '''
    replicas[0].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("bar"))
    replicas[1].crashed = replicas[2].crashed = True
    replicas[0].me.client_request(appstate.Cmd("foo"))
    replicas[1].crashed = replicas[2].crashed = False
    replicas[0].me.client_request(appstate.Cmd("baz"))

    replicas[0].crashed = True
    replicas[1].me.timeout()
    replicas[1].me.client_request(appstate.Cmd("fuzz"))

    for r in replicas:
        print r.me.consensus.progstate

def test_notleader(replicas):
    replicas[0].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("bar"))

    replicas[1].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("foo"))

    for r in replicas:
        print r.me.consensus.progstate


def test_many(replicas):
    go(lambda: replicas[0].me.timeout())
    time.sleep(.1)
    N = 1000
    def f():
        for i in xrange(N):
            time.sleep(.01)
            go(lambda: replicas[0].me.client_request(appstate.Cmd('c' + str(i))))
    go(f)
    time.sleep(2)
    go(lambda: replicas[1].me.timeout())

    time.sleep(3)
    go(lambda: replicas[1].me.client_request(appstate.Cmd('final')))
    time.sleep(5)
    for r in replicas:
        print r.me.consensus.progstate

def main():
    replicas = []
    for i in xrange(N):
        progstate = logprogstate.LogProgstate(appstate.LogDB())
        consensus = multiconsensus.MultiConsensus(i, progstate, 
                                                  1 if START_MASTER else 0, N)
        initialize(consensus)
        handler = eventhandler.EventHandler(consensus, None)
        net = fakenetworkdebug.FakeNetworkDebug(None, handler)
        handler.network = net

        replicas.append(net)

    for r in replicas:
        r.config = replicas


    test_many(replicas)
#    test_notleader(replicas)
#    test_gap(replicas)
#    test_recovery(replicas)
#    test_mismatchedlogs(replicas)

    return

    replicas[0].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("bar"))
    replicas[0].crashed = True

    replicas[1].me.timeout()
    replicas[1].me.client_request(appstate.Cmd("foo"))
    replicas[1].me.client_request(appstate.Cmd("baz"))

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
