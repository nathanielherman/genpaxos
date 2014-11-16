import threading
import time
import Queue
from multiconsensus import *

class EventHandler(object):
    def __init__(self, consensus, network, certifics_chan, snapshots_chan):
        self.consensus = consensus
        self.certifics_chan = certifics_chan
        self.snapshots_chan = snapshots_chan
        self.network = network
        self.certifics = set()
        self.snapshots = set()
        nop = lambda item: False
        self.handler_map = {'certify': self.certify_request, 'certifyResponse': self.certify_response,
                            'snapshot': self.snapshot_request, 'supportRound': self.supportRound_request, 'nop': nop}
        #threading.Thread(target=self.chan_handler).start()

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

    def client_request(self, value):
        print 'run', value
        # TODO: if not master, respond to client telling them who is
        send = self.consensus.certifySeq(self.consensus.rid, value)
        if send:
            # we always certify our own commands 
            # (TODO: should this be handled differently?)
            # we could do this by sending ourself a pseudo-network request
            # BUT this won't work right now because certifySeq adds this command
            # to our progsum already... probably should be all or nothing
            self.certifics.add((self.consensus.cert, self.consensus.rid, value))
            self.network.sendAll(send, self.response)

    def certify_response(self, (cert, rid, value)):
        if self.consensus.isSeq:
            self.certifics.add((cert, rid, value))
            self.consensus.observeDecision(value, self.certifics)
            resps = self.consensus.tryUpdates()
            if resps:
                print 'command result(s): ', resps
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

    def decide_request(self, value):
        self.consensus.observeDecision(value, leaderDecided=True)
        self.consensus.tryUpdates()

    def supportRound_request(self, (rid, proseq)):
        resp = self.consensus.supportRound(rid, proseq)
        return resp

    def timeout(self):
        new_rid = ((self.consensus.rid+1) << 8) | self.consensus.cert
        our_resp = self.consensus.supportRound(new_rid, self.consensus.cert)
        assert our_resp
        self.snapshots.add(our_resp[1])
        self.network.sendAll(('supportRound', (new_rid, self.consensus.cert)), self.response)

    def send_certify(self, item):
        assert 0
        self.network.send(self.consensus.proseq, 'certify', item)

    def send_snapshot(self, item):
        self.network.send(item[2], 'snapshot', item)

    def chan_handler(self):
        chans = [self.certifics_chan, self.snapshots_chan]
        chan_funcs = [self.send_certify, self.send_snapshot]
        ind = 0
        while 1:
            try:
                item = chans[ind].get_nowait()
                print 'got event'
                chan_funcs[ind](item)
            except Queue.Empty:
                if ind == len(chans)-1:
                    time.sleep(.1)
            ind = (ind + 1) % len(chans)
