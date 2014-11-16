import Queue
import threading

class Future(object):
    def __init__(self, sequential, fn, *args, **kwargs):
        if sequential:
            self.ran = True
            self.res = fn(*args, **kwargs)
            return

        self.fn = fn
        self.chan = Queue.Queue()
        self.ran = False
        self.res = None
        def run():
            ret = self.fn(*args, **kwargs)
            self.chan.put(ret)
        threading.Thread(target=run).start()

    def result(self):
        if not self.ran:
            self.ran = True
            self.res = self.chan.get()
        return self.res
    
