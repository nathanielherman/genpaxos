class Cmd(object):
    def __init__(self, s=None):
        self.s = s
    def __repr__(self):
        return 'cmd' + repr(self.s)
    def __eq__(self, c2):
        return self.s == c2.s

    def empty(self):
        return self.s == None

# mostly for debugging, this "database" simply keeps a list of all exec'd
# commands
class LogDB(object):
    nop = 'NOP'
    def __init__(self):
        self.log = []
    def __repr__(self):
        return repr(self.log)
    def __eq__(self, ld2):
        return self.log == ld2.log
    def __hash__(self):
        return 0

    # hmmm this is a little confusing? 
    def emptyCommand(self):
        return Cmd()
    def nopCommand(self):
        return Cmd(self.nop)

    def execute(self, cmd):
        assert not cmd.empty()
        if cmd.s != self.nop:
            self.log.append(cmd)

        return 'Success-' + repr(cmd)

    def contains(self, cmd):
        return cmd in self.log
