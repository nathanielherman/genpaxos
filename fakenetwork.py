
class FakeNetwork(object):
    # config should be an array of Network's indexed by their certifier id
    def __init__(self, config, me):
        self.config = config
        # our eventhandler
        self.me = me

    def sendAll(self, (msg, item), callback):
        resps = []
        replicas = range(len(self.config))
        while len(replicas):
            node = replicas.pop(0)
            if self.me.consensus.cert == node:
                continue
            # TODO: these should get sent async
            resp = self.send(node, msg, item)
            if resp:
                callback(resp)
            else:
                # keep trying
                replicas.append(node)

    def receive(self, msg, item):
        print 'recv'
        resp = self.me.request((msg, item))
        return resp

    # send does an actual network "send"
    def send(self, node, msg, item):
        # our fake network calls a node's network.receive() directly
        resp = self.config[node].receive(msg, item)
        # retry if returns None?
        # how distinguish network failure and a replica saying fuck off
        return resp
