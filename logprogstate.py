from collections import defaultdict
import copy
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

class Progsum(dict):
    default_factory = None

    def __getitem__(self, y):
        try:
            return super(Progsum, self).__getitem__(y)
        except KeyError:
            return self.default_factory()

    def consolidate(self, ps2):
        ret = copy.copy(self)
        for slot, val in ps2.iteritems():
            if val.rid > ret[slot].rid:
                ret[slot] = val
        return ret
    
    def updateRid(self, rid):
        def upd(slot):
            self[slot].rid = rid
        map(upd, self)

    def fillGaps(self, ridcmd):
        expected_slot = 0
        for slot in sorted(self.keys()):
            while expected_slot < slot and self[expected_slot].cmd.empty():
                self[expected_slot] = ridcmd
                expected_slot += 1
            expected_slot = slot+1


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
        
        self.next_slot = 0

    def __repr__(self):
        return "appState: %s; version: %d; log: %s; learned: %s" \
            % (repr(self.appState), self.version, repr(self.progsum), \
                   repr(self.learned))

    def set(self, new_progsum, rid):
        new_progsum.updateRid(rid)
        # fill in gaps with no ops
        new_progsum.fillGaps(RidCmd(rid, self.appState.nopCommand()))
        self.progsum = new_progsum
        return self

    def seq_certifiable(self, rid, value):
        # TODO: is this actually sufficient
        print 'seq_cert %d %s %s' % (value.slot, repr(self.progsum[value.slot].cmd), 
                                     repr(self.progsum[value.slot - 1].cmd))
        return self.progsum[value.slot].cmd.empty() and \
            (value.slot == 0 or not self.progsum[value.slot - 1].cmd.empty())

    def certifiable(self, rid, value):
        print 'certifiable', rid >= self.progsum[value.slot].rid
        if rid == self.progsum[value.slot].rid:
            assert value.cmd == self.progsum[value.slot].cmd
        # we actually do allow recertifying commands (this 
        # should be effectively the same as our certify message getting
        # duplicated)
        return rid >= self.progsum[value.slot].rid

    def certify(self, rid, value):
       self.progsum[value.slot] = RidCmd(rid, value.cmd)

    def sendable(self):
        return self.progsum

    def learn(self, value):
        self.learned[value.slot] = value.cmd

    def execableValues(self):
        prev = None
        next = self.learned.get(self.version, self.learned.default_factory())
        while not next.empty() and next != prev:
            yield SlottedValue(self.version, next)
            prev = next
            next = self.learned.get(self.version, self.learned.default_factory())

    def needsExec(self, value):
        return value.cmd == self.learned[self.version] \
            and not value.cmd.empty()

    def execute(self, value):
        result = self.appState.execute(value.cmd)
        self.version += 1
        return result

    def cert_values(self):
        vals = []
        for slot, val in self.progsum.iteritems():
            vals.append(SlottedValue(slot, val.cmd))
        return vals

    # ehhh
    def full_value(self, cmd):
        # in case we weren't the master, etc, etc.
        while not self.progsum[self.next_slot].cmd.empty():
            self.next_slot += 1
        ret = SlottedValue(self.next_slot, cmd)
        self.next_slot += 1
        return ret
