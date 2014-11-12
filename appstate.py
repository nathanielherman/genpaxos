class Cmd(object):
    def __init__(self, s=None):
        self.s = s

    def empty(self):
        return self.s == None

# mostly for debugging, this "database" simply keeps a list of all exec'd
# commands
class LogDB(object):
    def __init__(self):
        self.log = []

    def emptyCommand(self):
        return Cmd()

    def execute(self, cmd):
        assert not cmd.empty()
        log.append(cmd)
