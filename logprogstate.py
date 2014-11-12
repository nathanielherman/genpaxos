from collections import defaultdict
import multiconsensus


class RidCmd:
    def __init__(self, rid, cmd):
        self.rid = rid
        self.cmd = cmd

class LogProgstate(multiconsensus.Progstate):
    class Progsum(defaultdict):
        def consolidate(self, ps2):
            ret = self.copy()
            for slot, val in ps2:
                if val.rid > ret[slot].rid:
                    ret[slot] = val
            return ret

    def __init__(self, appState, version=0):
        self.appState = appState
        self.version = version
        self.progsum = Progsum()
        self.progsum.default_factory = lambda: RidCmd(0, appState.emptyCommand())
        self.learned = defaultdict()
        self.learned.default_factory = lambda: appState.emptyCommand()

    def seq_certifiable(self, rid, value):
        # TODO: is this actually sufficient
        return self.progsum[value.slot].cmd.empty() and \
            not self.progsum[value.slot - 1].cmd.empty()

    def certifiable(self, rid, value):
        return rid > self.progsum[value.slot].rid

    def certify(self, rid, value):
       self.progsum[value.slot] = RidCmd(rid, value.cmd)

    def sendable(self):
        return self.progsum

    def learn(self, value):
        self.learned[value.slot] = value.cmd

    def needsExec(self, value):
        return value.cmd == self.learned[self.version] \
            and not value.cmd.empty()

    def execute(self, value):
        result = self.appState.execute(value.cmd)
        self.version += 1
        return result
