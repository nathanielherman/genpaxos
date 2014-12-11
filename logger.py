Debug = 0
Info = 1
Error = 2
Nothing = 3
level = Debug
class Logger(object):
    level = Debug
    def log(self, level, *args, **kwargs):
        if level >= self.level:
            s = ' '.join([str(a) for a in args])
            print s

default_logger = Logger()

def log(lvl, *args, **kwargs):
    default_logger.level = level
    default_logger.log(lvl, *args, **kwargs)

