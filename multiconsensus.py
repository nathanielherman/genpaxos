from collections import defaultdict
from conditions import precondition

import threading

import functools
def protected(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        self.lock()
        retval = func(self, *args, **kwargs)
        self.unlock()
        return retval
    return wrapper

class ActiveRep(object):
    def __init__(self, progstate):
        self.progstate = progstate
        self.big_lock = threading.Lock()

    def lock(self):
        self.big_lock.acquire()
    def unlock(self):
        self.big_lock.release()

    @precondition(lambda self, value: self.progstate.needsExec(value))
    def _update(self, value):
        result = self.progstate.execute(value)
        return result

    update = protected(_update)

    @protected
    def tryUpdates(self):
        resps = []
        for val in self.progstate.execableValues():
            resps.append(self._update(val))
        return resps


class MultiConsensus(ActiveRep):
    def __init__(self, cert, progstate, rid, n):
        super(MultiConsensus, self).__init__(progstate)
        self.rid = rid
        self.isSeq = False
        # this is sort of just an approximation (and can probably be transient state)
        self.proseq = -1
        self.cert = cert
        self.n = n
        self.certifics = set()
        self.snapshots = set()

    @protected
    def add_certific(self, item):
        self.certifics.add(item)
    @protected
    def add_snapshot(self, item):
        self.snapshots.add(item)

    @protected
    @precondition(lambda self, rid, proseq: rid > self.rid)
    def supportRound(self, rid, proseq):
        self.rid = rid
        self.isSeq = False
        self.proseq = proseq
        return ('snapshot', (self.cert, rid, proseq, self.progstate.sendable()))

    def _subset(self, S, rid, cert, snapshots):
        # literal from the paper
        Ssuper = set()
        for sn in snapshots:
            if sn[1] != rid or sn[2] != cert:
                continue
            Ssuper.add((sn[0], sn[3]))
        return S.issubset(Ssuper)

    def _supporters(self, rid, cert, snapshots):
        support = {}
        for sn in snapshots:
            if sn[1] != rid or sn[2] != cert:
                continue
            support[sn[0]] = sn[3]
        return support.values()

    # network precondition: S is a subset of snapshot messages received and
    # only includes messages matching our rid and with us as proseq
    @protected
    @precondition(lambda self, rid: self.rid == rid and not self.isSeq and \
                  len(self._supporters(rid, self.cert, self.snapshots)) > self.n/2)
    def recover(self, rid):
        support = self._supporters(rid, self.cert, self.snapshots)
        consolidated = reduce(lambda ps1, ps2: ps1.consolidate(ps2), support)
        self.progstate = self.progstate.set(consolidated, self.rid)
        # this can only happen AFTER we set progstate!!
        self.isSeq = True
        
        cert_vals = self.progstate.cert_values()
        # TODO: maybe what we really want is for this to call certifySeq?
        return [('certify', (self.cert, self.rid, v)) for v in cert_vals]

    @protected
    @precondition(lambda self, rid, value: self.isSeq and rid == self.rid \
                 #and value in inputs
                 and self.progstate.seq_certifiable(rid, value))
    def certifySeq(self, rid, value):
        print 'certseq'
        value = self.progstate.full_value(value)
        # we don't currently actually certify here, though we could
        # instead we let the network implicitly do it (unclear which is really better)
        return ('certify', (self.cert, rid, value))

    # network precondition: someone else has certified this command
    @protected
    @precondition(lambda self, rid, value: 
                  self.rid == rid and self.progstate.certifiable(rid, value))
    def certify(self, rid, value):
        self.progstate.certify(rid, value)
        print 'certify'
        return ('certifyResponse', (self.cert, rid, value))
#        self.certifics_chan.put((self.cert, rid, value))

    # returns how many certifiers (in a single given round) support this particular value
    # (I guess this is a Raft-like definition)
    def _roundSupport(self, certifics, value):
        # filter to only certifications of this particular value
        cs = filter(lambda c: c[2] == value, certifics)
        dict = defaultdict(lambda: 0)
        for (_, rid, _) in cs:
            dict[rid] += 1
        return max(dict.values())

    # network precondition: a majority of nodes have certified this command.
    # we know this either because: we're the master and we actually hear back
    # from a majority, OR we're a follower and the master told us a majority
    # had certified the command
    @protected
    @precondition(lambda self, value, leaderDecided=False: 
                  leaderDecided or 
                  (self._roundSupport(self.certifics, value) > self.n/2))
    def observeDecision(self, value, leaderDecided=False):
        self.progstate.learn(value)
        if self.isSeq:
            return ('decide', (value))

class Progstate:
    def consolidate(self, progstate2):
        pass
    def set(self, new_progstate):
        return new_progstate
    def seq_certifiable(self, rid, value):
        pass
    def certifiable(self, rid, value):
        pass
    def certify(self, rid, value):
        pass
    def sendable(self):
        return self
    def learn(self, value):
        pass
    def execute(self, value):
        return value
    def needsExec(self, value):
        return False
