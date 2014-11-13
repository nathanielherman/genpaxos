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
        self.handler_map = {'certify': self.certify_request, 'snapshot': self.snapshot_request}
        threading.Thread(target=self.chan_handler).start()

    def request(self, msg, item):
        return self.handler_map[msg](item)

    def client_request(self, value):
        print 'run'
        # TODO: if not master, respond to client telling them who is
        self.consensus.certifySeq(self.consensus.rid, value)

    def certify_request(self, (cert, rid, value)):
        if self.consensus.isSeq:
            self.certifics.add((cert, rid, value))
            if self.consensus._roundMajority(self.certifics, value):
                self.consensus.observeDecision(value)
                resp = self.consensus.update(value)
                print 'resp: ', resp
        else:
            resp = self.consensus.certify(rid, value)
            print 'client_resp', resp
            return resp

    def snapshot_request(self, item):
        print 'snapshot_Request'

    def decide_request(self, value):
        self.consensus.observeDecision(value)

    def supportRound_request(self, rid, proseq):
        self.consensus.supportRound(rid, proseq)

    def timeout(self):
        pass

    def send_certify(self, item):
        if self.consensus.isSeq:
            # TODO: this is a relatively complex part of the app
            # we need to wait for a majority synchronously, but then
            # continue resending other requests async
            resps = self.network.sendAll('certify', item)
            map(lambda r: self.certify_request(r[1]), resps)
        else:
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
