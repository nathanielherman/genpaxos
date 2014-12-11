import copy
import logprogstate

class FullProgstate(logprogstate.LogProgstate):
    def __init__(self, appState, version=0):
        super(FullProgstate, self).__init__(appState, version)
        self.snapshot = None

    def sendable(self):
        # do we send appState or snapshot?
        return AppProgsum(self.appState, self.version, self.progsum)

    # we should be locked at this point
    def take_snapshot(self):
        snapshot = self.appState.snapshot(self.version)
        # we update snapshot, THEN we can truncate log
        self.snapshot = snapshot
        self.progsum.truncate(self.version)

    def set(self, new_progsum, rid):
        self.appState = new_progsum.appState
        self.version = new_progsum.version
        super(FullProgstate, self).set(new_progsum.progsum, rid)
        return self

    def updateAppState(self, newAS, rid):
        self.appState = newAS.appState
        self.version = newAS.version
        # ALMOST identical to set() except we merge with our current log
        # rather than replacing (in case we've certified new commands since)
#        super(FullProgstate, self).updateAppState(newAS.progsum, rid)
        # TODO: should we truncate now or wait til a snapshot? [or ask for a snapshot now]
        # there's a slightly weird thing where our log before self.version
        # could be totally wrong. it seems like this doesn't matter but it's weird
        self.progsum.truncate(self.version)

# unlike the log summary, we only construct these objects
# during a view change
class AppProgsum(object):
    def __init__(self, appState, version, progsum):
        self.appState = appState
        self.version = version
        self.progsum = progsum

    def consolidate(self, ps2):
        ret = copy.copy(self)
        if ret.version < ps2.version:
            ret.appState = ps2.appState
            ret.version = ps2.version
            ret.progsum.truncate(ret.version)
        else:
            ps2.progsum.truncate(ret.version)

        ret.progsum = ret.progsum.consolidate(ps2.progsum)
        return ret
