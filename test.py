#!/usr/bin/python
import os
import random
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
from replica import *
import Queue

N = 3
START_MASTER = -1

def go(f):
    #f()
    threading.Thread(target=f).start()

def print_replicas(replicas):
    map(print_replica, replicas)

def gen_replicas(N):
    reps = []
    for i in xrange(N):
        reps.append(make_replica(i, N, START_MASTER))

    for r in reps:
        r.config = reps

    return reps

def coms(l):
    return [appstate.Cmd(s) for s in l]

def test_recovery():
    '''Tests whether replicas with out of date state can keep participating successfully

    Expected outcome:
    fuzz gets successfully committed (but will only be in 0's appstate)
    1 has fuzz in the log but not committed
    2 has everything before fuzz in log (because it crashes then)'''
    replicas = gen_replicas(3)

    replicas[0].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("bar"))
    replicas[1].crashed = True
    replicas[0].me.client_request(appstate.Cmd("foo"))
    replicas[1].crashed = False
    replicas[0].me.client_request(appstate.Cmd("baz"))
    replicas[2].crashed = True
    replicas[0].me.client_request(appstate.Cmd("fuzz"))

    #replicas[1].me.timeout()

    assert check_appstate(replicas)
    assert replicas[1].me.consensus.progstate.contains(appstate.Cmd("fuzz"))

def test_mismatchedlogs():
    '''Tests whether recovery works in the case where different replicas disagree on logs

    Expected outcome:
    everyone puts bar2 in their appstate, bar gets obliterated
    (replica 1 will have an out of date rid for it)'''
    replicas = gen_replicas(3)

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

    assert replicas[0].me.consensus.progstate.contains(appstate.Cmd("bar2"))
    assert not replicas[0].me.consensus.progstate.contains(appstate.Cmd("bar"))
    # replica 1 is down so its round id will be out of date
    assert check_replicas(replicas, [[0,2]])
    assert check_groups(replicas, grouper=appstate_groups)

def test_gap():
    '''Tests whether gaps in the log successfully get filled with NOPs

    Expected outcome:
    slot 1 gets replaced with a NOP, giving final appstate
    ['bar','baz','fuzz'] for 1 and 2, but just 'bar' for 0 (who crashes)
    '''
    replicas = gen_replicas(3)
    replicas[0].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("bar"))
    replicas[1].crashed = replicas[2].crashed = True
    replicas[0].me.client_request(appstate.Cmd("foo"))
    replicas[1].crashed = replicas[2].crashed = False
    replicas[0].me.client_request(appstate.Cmd("baz"))

    replicas[0].crashed = True
    replicas[1].me.timeout()
    replicas[1].me.client_request(appstate.Cmd("fuzz"))

    assert replicas[1].me.consensus.progstate.appState.log == coms(['bar', 'baz', 'fuzz'])
    assert check_replicas(replicas, [[1,2]])
    assert check_groups(replicas, [[1,2]], appstate_groups)
    
def test_notleader(nreps=3):
    replicas = gen_replicas(nreps)
    replicas[0].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("bar"))

    replicas[1].me.timeout()
    replicas[0].me.client_request(appstate.Cmd("foo"))

    assert replicas[1].me.consensus.progstate.appState.log == coms(['bar'])
    assert check_replicas(replicas, [[1,2]])

def test_many(nreps=3):
    replicas = gen_replicas(nreps)


    go(lambda: replicas[0].me.timeout())
    time.sleep(.1)
    reqs = 1000
    def f():
        for i in xrange(reqs):
            time.sleep(.01)
            go(lambda: replicas[0].me.client_request(appstate.Cmd('c' + str(i))))
    go(f)
    time.sleep(2)
    go(lambda: replicas[1].me.timeout())

    time.sleep(3)
    go(lambda: replicas[1].me.client_request(appstate.Cmd('final')))
    time.sleep(5)

    assert check_replicas(replicas)

def test_rand(nreps=3, runtime=10, seed=0, crash_freq=.1, crash_skew=.5, client_freq=.01, timeout_freq=.1):
    replicas = gen_replicas(nreps)
    done = False

    def crasher():
        downreps = 0
        rand = random.Random(seed)
        while not done:
            time.sleep(crash_freq)
            crash = rand.random() < crash_skew
            # nothing to bring up
            if not crash and downreps == 0:
                continue
            # we'll lose a majority if we crash another
            if crash and downreps >= nreps/2:
                continue
            rep = rand.choice(replicas)
            if rep.crashed == crash:
                continue
            rep.crashed = crash
            downreps += 1 if crash else -1

    def client(id=0):
        rand = random.Random(seed+id)
        i = 0
        while not done:
            time.sleep(client_freq)
            # racey (but shouldn't really matter?)
            r = find_master(replicas)
            if not r:
                continue
            c = '%d,%d' % (id, i)
            r.me.request(('client', appstate.Cmd(c)))
            i += 1

    def timeout(id=0):
        rand = random.Random(seed+id)
        while not done:
            time.sleep(timeout_freq)
            rep = rand.choice(replicas)
            rep.me.timeout()

    replicas[0].me.timeout()
    go(client)
    go(crasher)
    go(timeout)
    go(lambda: timeout(1))

    time.sleep(runtime)
    done = True
    time.sleep(2)
    for rep in replicas:
        rep.crashed = False
    replicas[0].me.timeout()
    replicas[0].me.timeout()
    replicas[0].me.timeout()
    replicas[0].me.timeout()
    replicas[0].me.timeout()

    assert check_appstate(replicas)
    assert check_replicas(replicas)

    print_replicas(replicas)

def main():
    replicas = gen_replicas(N)

    test_rand()
    return

    test_many()
    time.sleep(1)
    test_notleader()
    time.sleep(1)
    test_gap()
    time.sleep(1)
    test_recovery()
    time.sleep(1)
    test_mismatchedlogs()
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
