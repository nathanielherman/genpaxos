from fakenetwork import *

class FakeNetworkDebug(FakeNetwork):
    crashed = False

    def send(self, node, msg, item):
        if self.crashed:
            return Future(True, lambda: None)
        return super(FakeNetworkDebug, self).send(node, msg, item)

    def receive(self, msg, item):
        if self.crashed:
            return None
        return super(FakeNetworkDebug, self).receive(msg, item)

