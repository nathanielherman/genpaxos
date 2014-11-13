from collections import defaultdict
from conditions import precondition

class ActiveRep(object):
    def __init__(self, progstate):
        self.progstate = progstate

    @precondition(lambda self, value: self.progstate.needsExec(value))
    def update(self, value):
        result = self.progstate.execute(value)
        return result


class MultiConsensus(ActiveRep):
    def __init__(self, cert, progstate, rid, n, 
                 certifics_chan, snapshots_chan):
        super(MultiConsensus, self).__init__(progstate)
        self.rid = rid
        self.isSeq = False
        # this is sort of just an approximation (and can probably be transient state)
        self.proseq = -1
        self.cert = cert
        self.n = n
        self.certifics_chan = certifics_chan
        self.snapshots_chan = snapshots_chan

    @precondition(lambda self, rid, proseq: rid > self.rid)
    def supportRound(self, rid, proseq):
        self.rid = rid
        self.isSeq = False
        self.proseq = proseq
        self.snapshots_chan.put((self.cert, rid, proseq, self.progstate.sendable()))

    def _subset(self, S, rid, cert, snapshots):
        # literal from the paper
        Ssuper = set()
        for sn in snapshots:
            if sn[1] != rid or sn[2] != cert:
                continue
            Ssuper.add((sn[0], sn[3]))
        return S.issubset(Ssuper)

    # network precondition: S is a subset of snapshot messages received and
    # only includes messages matching our rid and with us as proseq
    @precondition(lambda self, rid, S: self.rid == rid and not self.isSeq and \
                  len(S) > self.n/2)
    def recover(self, rid, S):
        self.progstate.set(reduce(lambda ps1, ps2: ps1.consolidate(ps2), S))
        self.isSeq = True

    @precondition(lambda self, rid, value: self.isSeq and rid == self.rid \
                 #and value in inputs
                 and self.progstate.seq_certifiable(rid, value))
    def certifySeq(self, rid, value):
        print 'certseq'
        self.progstate.certify(rid, value)
        self.certifics_chan.put((self.cert, rid, value))

    # network precondition: someone else has certified this command
    @precondition(lambda self, rid, value: 
                  self.rid == rid and self.progstate.certifiable(rid, value))
    def certify(self, rid, value):
        self.progstate.certify(rid, value)
        print 'certify'
        return ('certify', (self.cert, rid, value))
#        self.certifics_chan.put((self.cert, rid, value))

    def _roundMajority(self, certifics, value):
        cs = filter(lambda c: c[2] == value, certifics)
        dict = defaultdict(lambda: 0)
        for (_, rid, _) in cs:
            dict[rid] += 1
        return max(dict.values())

    # network precondition: a majority of nodes have certified this command
    @precondition(lambda self, value: True)
    def observeDecision(self, value):
        self.progstate.learn(value)

class Progstate:
    def consolidate(self, progstate2):
        pass

    def set(self, new_progstate):
        self = new_progstate

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
