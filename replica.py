from collections import defaultdict
import multiconsensus
import fakenetwork
import fakenetworkdebug
import logprogstate
import eventhandler
import appstate

def make_replica(i, N, start_master=-1):
    progstate = logprogstate.LogProgstate(appstate.LogDB())
    init_rid = (1<<8 | start_master) if start_master >= 0 else 0
    consensus = multiconsensus.MultiConsensus(i, progstate,
                                              init_rid, N)
    if start_master >= 0:
        consensus.proseq = start_master
        consensus.isSeq = consensus.proseq == consensus.cert

    handler = eventhandler.EventHandler(consensus, None)
    net = fakenetworkdebug.FakeNetworkDebug(None, handler)
    handler.network = net

    return net

def print_replica(replica):
    print replica.me.consensus.progstate

def rgroups(replicas, f):
    d = defaultdict(lambda: set())
    for r in replicas:
        d[f(r)].add(r.me.consensus.cert)
    return dict(d)

def log_groups(replicas): return rgroups(replicas, lambda r: r.me.consensus.progstate.progsum)
def appstate_groups(replicas): return rgroups(replicas, lambda r: r.me.consensus.progstate.appState)

def find_master(replicas):
    (rid, master) = -1, None
    for r in replicas:
        if r.me.consensus.isSeq and r.me.consensus.rid >= rid:
            assert r.me.consensus.rid != rid
            (rid, master) = r.me.consensus.rid, r
    return master

def expected_appstate(replicas):
    r = find_master(replicas)
    log = r.me.consensus.progstate.progsum
    max_entry = max(log.keys())
    expectedAS = appstate.LogDB()
    for i in xrange(max_entry+1):
        if log[i].cmd.empty():
            continue
        expectedAS.execute(log[i].cmd)
    return expectedAS

def check_appstate(replicas):
    expect = expected_appstate(replicas)
    real = find_master(replicas).me.consensus.progstate.appState
    if not (real == expect):
        print 'unexpected appstate:'
        print 'expected: ', expect
        print 'got: ', real
        assert 0
        return False
    return True

def check_groups(replicas, same=None, grouper=log_groups):
    if not same:
        same = [range(len(replicas))]
    lg = grouper(replicas)
    for group in same:
        if not any([set(group).issubset(g) for g in lg.values()]):
            print 'unexpected groupings:'
            print lg
            return False
    return True


def check_replicas(replicas, same=None, master_committed=True, check_appstate_groups=False):
    if not check_groups(replicas, same):
        return False

    if master_committed and not check_appstate(replicas):
        return False
    if check_appstate_groups and not check_groups(replicas, same, appstate_groups):
        return False

    return True
