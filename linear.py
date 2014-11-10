from conditions import precondition

class ActiveRep:
    def __init__(self, progstate):
        self.progstate = progstate
        self.version = 0
        self.learned = defaultdict()
        self.learned.default_factory = lambda: appState.emptyCommand()

    @precondition(lambda value: self.progstate.needsUpdate(value))
    def update(value):
        result = self.progstate.execute(value)
        outputs.append(result)
        self.progstate.update(value, result)


class MultiConsensus(ActiveRep):
    def __init__(self, cert, progstate, rid):
        super.__init__(progstate)
        self.rid = rid
        self.isSeq = False
        self.cert = cert

    @precondition(lambda rid, proseq: rid > self.rid)
    def supportRound(rid, proseq):
        self.rid = rid
        self.isSeq = False
        snapshots.append(self.cert, rid, proseq, self.progstate.sendable())
        
    @precondition(lambda rid, S: self.rid == rid and not self.isSeq and
                  len(S) > n/2 and )
    def recover(rid, S):
        self.progstate.set(reduce(lambda ps1, ps2: ps1.consolidate(ps2), S))
        self.isSeq = True

    @preconditon(lambda rid, value: self.isSeq and rid = self.rid and
                 value in inputs and progstate.seq_certifiable(rid, value))
    def certifySeq(rid, value):
        progstate.certify(rid, value)
        certifics.append(self.cert, rid, value)

    @precondition(lambda rid, value: (cert, rid, value) in certifics
                  and self.rid = rid and progstate.certifiable(rid, value))
    def certify(rid, value):
        progstate.certify(rid, value)
        certifics.append(self.cert, rid, value)

    @precondition(lambda value: majority response)
    def observeDecision(value):
        self.update(value)

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

    def execute(self, value):
        return value

    def needsUpdate(self, value):
        return False

    def update(self, value, result):
        pass

