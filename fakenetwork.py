
class FakeNetwork(object):
    # config should be an array of EventHandler's indexed by their certifier id
    def __init__(self, config):
        self.config = config

    def sendAll(self, msg, item):
        for n in self.config:
            self.send(n, msg, item)

    # send does an actual network "send"
    def send(self, node, msg, item):
        # our fake network calls request directly
        self.config[node].request(msg, item)
