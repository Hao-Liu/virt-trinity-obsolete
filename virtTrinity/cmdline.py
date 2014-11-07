import utils


class CmdLine(object):

    def __init__(self, command, random=True):
        self.command = command
        self.options = []
        if random:
            self.name = command.short_name
            self.options = [
                {
                    "option": opt,
                    "line": opt.random(),
                }
                for opt in command.options
            ]

    def __str__(self):
        cmd_line = 'virsh ' + self.name
        for option in self.options:
            if option['line'] is None:
                continue
            else:
                result_line = '--' + option['option'].name
                if option['line']:
                    result_line += ' %s' % utils.escape(option['line'])
                cmd_line += ' %s' % result_line
        return cmd_line

    def run(self, timeout=60):
        return utils.run(str(self), timeout=timeout)
