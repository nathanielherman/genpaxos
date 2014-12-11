Debug = 0
Info = 1
Error = 2
class Logger(object):
    self.level = Debug
    def debug(self, level, *args, **kwargs):
        if level >= self.level:
            s = '\n'.join([repr(a) for a in args])
            print s

logger = Logger()
