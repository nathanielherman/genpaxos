import Queue
import threading

class Future(object):
    def __init__(self, sequential, fn, *args, **kwargs):
        if sequential:
            self.res = fn(*args, **kwargs)
            return

        self.fn = fn
        self.chan = Queue.Queue()
        self.res = None
        def run():
            print 'calling'
            ret = self.fn(*args, **kwargs)
            print 'completed'
            self.chan.put(ret)
            print 'exit'
        threading.Thread(target=run).run()

    def result(self):
        if not self.res:
            self.res = self.chan.get()
        return self.res
    
