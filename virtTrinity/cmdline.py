import utils


class VirshCmdResult(utils.CmdResult):
    @classmethod
    def from_result(cls, cmd_line, result):
        def sub(cmd_line, text):
            if type(text) == list:
                text = '\n'.join(text)

            text = text.decode('utf-8')
            for opt in cmd_line.options:
                line = opt['line']
                replacement = '${%s}' % opt['option'].name
                if line and line in text:
                    text = text.replace(line, replacement)
            return text
        result.__class__ = cls
        result.cmdname = cmd_line.name

        result.sub_stdout = sub(cmd_line, result.stdout)
        result.sub_stderr = sub(cmd_line, result.stderr)

        result.key = '\n'.join((
            result.exit_status,
            result.sub_stdout,
            result.sub_stderr,
        ))
        return result


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
        cmd_result = utils.run(str(self), timeout=timeout)
        return VirshCmdResult.from_result(self, cmd_result)
