import threading
import Queue
from multiconsensus import *

class EventHandler(object):
    handler_map = {'certify': certify_request, 'snapshot': snapshot_request}

    def __init__(self, consensus, network, certifics_chan, snapshots_chan):
        self.consensus = consensus
        self.certifics_chan = certifics_chan
        self.snapshots_chan = snapshots_chan
        self.network = network
        self.certifics = set()
        self.snapshots = set()
        threading.Thread(target=self.chan_handler).start()

    def request(self, msg, item):
        handler_map[msg](item)

    def client_request(self, value):
        # TODO: if not master, respond to client telling them who is
        self.consensus.certifySeq(rid, value)

    def certify_request(self, (cert, rid, value)):
        if self.consensus.isSeq:
            self.certifics.add((cert, rid, value))
        else:
            self.consensus.certify(rid, value)

    def decide_request(self, value):
        self.consensus.observeDecision(value)

    def supportRound_request(self, rid, proseq):
        self.consensus.supportRound(rid, proseq)

    def timeout(self):
        pass

    def send_certify(self, item):
        if self.consensus.isSeq:
            self.network.sendAll('certify', item)
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
                chan_funcs[ind](item)
            except Queue.Empty:
                if ind == len(chans)-1:
                    time.sleep(.1)
            ind = (ind + 1) % len(chans)
