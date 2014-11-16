from collections import defaultdict
import multiconsensus


class RidCmd:
    def __init__(self, rid, cmd):
        self.rid = rid
        self.cmd = cmd
    def __repr__(self):
        return repr((self.rid, self.cmd))

class SlottedValue(object):
    def __init__(self, slot, cmd):
        self.slot = slot
        self.cmd = cmd
    def __repr__(self):
        return repr((self.slot, self.cmd))

class Progsum(defaultdict):
    def consolidate(self, ps2):
        ret = self.copy()
        for slot, val in ps2.iteritems():
            if val.rid > ret[slot].rid:
                ret[slot] = val
        return ret

    def __hash__(self):
        return 0


class LogProgstate(multiconsensus.Progstate):
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
            (value.slot == 0 or not self.progsum[value.slot - 1].cmd.empty())

    def certifiable(self, rid, value):
        print 'certifiable', rid > self.progsum[value.slot].rid
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

    def cert_messages(self, cert):
        msgs = []
        for slot, val in self.progsum.iteritems():
            msgs.append(('certify', (cert, val.rid, SlottedValue(slot, val.cmd))))
        return msgs
