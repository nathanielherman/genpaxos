from future import Future

class FakeNetwork(object):
    # config should be an array of Network's indexed by their certifier id
    def __init__(self, config, me):
        self.config = config
        # our eventhandler
        self.me = me

    def sendAll(self, (msg, item), callback):
        resps = []
        replicas = range(len(self.config))
        # TODO: we're sending to ourselves here (should turn into a no op)
        resps = map(lambda n: (n, self.send(n, msg, item)), replicas)
        retries = 0
        # not super ideal but basically this means that we'll try
        # each replica at least 3 times before giving up
        max_retries = len(replicas)*2+1
        while len(resps) and retries < max_retries:
            node, future = resps.pop(0)
            resp = future.result()
#            if self.me.consensus.cert == node:
 #               print 'callback', callback(resp)
  #              continue
            if resp:
                print 'node', self.me.consensus.cert, 'got response', resp
                # they don't need these to be sent anymore (or, possibly,
                # we could continue sending in the background)
                if callback(resp):
                    return
            else:
                # keep trying
                resps.append((node, self.send(node, msg, item)))
                retries += 1

    def receive(self, msg, item):
        print 'node ', self.me.consensus.cert, ' received ', msg, item
        resp = self.me.request((msg, item))
        return resp

    # send does an actual network "send"
    def send(self, node, msg, item):
        print 'node ', self.me.consensus.cert, ' send to ', node, msg, item
        # our fake network calls a node's network.receive() directly
        # retry if returns None?
        # how distinguish network failure and a replica saying fuck off
        print 'crashed', self.config[node].crashed
        return Future(False, self.config[node].receive, msg, item)
