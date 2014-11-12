import multiconsensus

class ValueProgstate(multiconsensus.Progstate):
    def __init__(self):
        self.value = None
        self.vrid = -1

    def __cmp__(self, ps2):
        return self.vrid.__cmp__(ps2.vrid)

    def consolidate(self, progstate2):
        if progstate2 > self:
            return progstate2
        return self

    def seq_certifiable(self, rid, value):
        # TODO: technically we should also check that this value's been proposed
        return self.value == None

    def certifiable(self, rid, value):
        return rid >= self.vrid

    def certify(self, rid, value):
        assert self.seq_certifiable(rid, value) or self.certifiable(rid, value)

        self.vrid = rid
        self.value = value

    #TODO: do we need to do anything when value is actually decided??
    def needsExec(self, value):
        return True
