
class FakeNetwork(object):
    # config should be an array of Network's indexed by their certifier id
    def __init__(self, config, me):
        self.config = config
        # our eventhandler
        self.me = me

    def sendAll(self, msg, item):
        resps = []
        for node in self.config:
            resp = self.send(node, msg, item)
            resps.append(resp)
        return resps

    def receive(self, msg, item):
        resp = self.me.request(msg, item)
        return resp

    # send does an actual network "send"
    def send(self, node, msg, item):
        # our fake network calls a node's network.receive() directly
        resp = self.config[node].receive(msg, item)
        # retry if returns None?
        return resp
