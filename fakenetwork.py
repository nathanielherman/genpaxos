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
        resps = map(lambda n: (n, self.send(n, msg, item)), replicas)
        while len(resps):
            node, future = resps.pop(0)
            if self.me.consensus.cert == node:
                continue
            resp = future.result()
            if resp:
                # they don't need these to be sent anymore (or, possibly,
                # we could continue sending in the background)
                if callback(resp):
                    return
            else:
                # keep trying
                resps.append((node, self.send(node, msg, item)))

    def receive(self, msg, item):
        print 'recv'
        resp = self.me.request((msg, item))
        return resp

    # send does an actual network "send"
    def send(self, node, msg, item):
        # our fake network calls a node's network.receive() directly
        # retry if returns None?
        # how distinguish network failure and a replica saying fuck off
        return Future(True, self.config[node].receive, msg, item)
