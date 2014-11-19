import threading
import time
import Queue
from multiconsensus import *

class EventHandler(object):
    def __init__(self, consensus, network):
        self.consensus = consensus
        self.network = network
        # TODO: maybe these should go inside consensus to get locking for free?
        self.certifics = set()
        self.snapshots = set()
        nop = lambda item: False
        self.handler_map = {'certify': self.certify_request, 'certifyResponse': self.certify_response,
                            'snapshot': self.snapshot_request, 'supportRound': self.supportRound_request, 
                            'decide': self.decide_request, 'nop': nop}

    def request(self, (msg, item)):
        resp = self.handler_map[msg](item)
        if not resp:
            resp = ('nop', 1)
        return resp

    def response(self, (msg, item)):
        # TODO: do we want to fully separate requests and responses?
        # is there ever a case where an rpc can be both?
        resp = self.handler_map[msg](item)
        return resp

    def client_request(self, cmd):
        print 'run', cmd
        # TODO: if not master, respond to client telling them who is
        send = self.consensus.certifySeq(self.consensus.rid, cmd)
        if send:
            # TODO: haven't totally decided whether we should certify our own commands by going through sendAll
            # like this or just doing it sorta manually. this way seems cleaner for the most part but is less efficient
            # technically
            self.network.sendAll(send, self.response)

    def certify_response(self, (cert, rid, value)):
        if self.consensus.isSeq:
            self.certifics.add((cert, rid, value))
            decide_resp = self.consensus.observeDecision(value, self.certifics)
            client_resps = self.consensus.tryUpdates()
            if client_resps:
                print 'command result(s): ', client_resps
            if decide_resp:
                self.network.sendAll(decide_resp, lambda item: True)
                return True

    def certify_request(self, (cert, rid, value)):
        resp = self.consensus.certify(rid, value)
        print 'cert_resp', resp
        return resp

    def snapshot_request(self, item):
        (cert, rid, proseq, state) = item
        self.snapshots.add(item)
        isseq = self.consensus.isSeq
        msgs = self.consensus.recover(rid, self.snapshots)
        ret = False
        if isseq == False and self.consensus.isSeq:
            print self.consensus.cert, ' became master'
            ret = True
        if msgs:
            for m in msgs:
                self.network.sendAll(m, self.response)
            ret = True
        return ret

    def decide_request(self, (value)):
        self.consensus.observeDecision(value, leaderDecided=True)
        self.consensus.tryUpdates()

    def supportRound_request(self, (rid, proseq)):
        resp = self.consensus.supportRound(rid, proseq)
        return resp

    def timeout(self):
        cur = self.consensus.rid >> 8
        new_rid = ((cur+1) << 8) | self.consensus.cert
        self.network.sendAll(('supportRound', (new_rid, self.consensus.cert)), self.response)
