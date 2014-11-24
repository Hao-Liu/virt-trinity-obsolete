import re
import json
import random
import subprocess
import pkg_resources
import itertools

import utils
import option


class Command(object):
    # pylint: disable=E1101
    settings = json.loads(
        pkg_resources.resource_string(
            __name__, 'data/virsh_option_types.json'))

    def __init__(self):
        self.options = {}
        self.synopsis = ''

    def _parse_options(self):
        options = {}
        if self.options:
            last_name = ''
            for opt_line in self.options:
                opt = option.Option.from_help(
                    opt_line, self.name)
                options[opt.name] = opt
                last_name = opt.name

        if '...' in self.synopsis:
            options[last_name].argv = True
        self.options = options

    @classmethod
    def from_help(cls, name):
        cmd = cls()
        help_txt = subprocess.check_output(
            ['virsh', 'help', name]).splitlines()

        item_name = ''
        item_content = []
        for line in help_txt:
            if re.match(r'^  [A-Z]*$', line):
                if item_name:
                    if item_name == 'options':
                        setattr(cmd, item_name, item_content)
                    else:
                        setattr(cmd, item_name, ''.join(item_content))
                    item_content = []
                item_name = line.strip().lower()
            else:
                if line:
                    item_content.append(line.strip())
        if item_name:
            if item_name == 'options':
                setattr(cmd, item_name, item_content)
            else:
                setattr(cmd, item_name, ''.join(item_content))
            item_content = []

        cmd.long_name = cmd.name
        cmd.name = name
        cmd._parse_options()

        settings = Command.settings
        if name in settings:
            for item, content in settings[name].items():
                if item == 'option_types':
                    for opt_name, opt_type in content.items():
                        cmd.options[opt_name].opt_type = opt_type
                else:
                    setattr(cmd, item, content)
        return cmd

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        cmd = cls()
        for key, value in json_dict.items():
            if key == 'options':
                options = {}
                for opt_name, opt_dict in value.items():
                    opt_json = json.dumps(opt_dict)
                    opt = option.Option.from_json(opt_json)
                    options[opt.name] = opt
                value = options
            setattr(cmd, key, value)
        return cmd

    def to_json(self):
        json_dict = {}
        for key in self.__dict__:
            value = getattr(self, key)
            if key == 'options':
                value = {}
                for name, opt in self.options.items():
                    value[name] = json.loads(opt.to_json())
            json_dict[key] = value

        return json.dumps(json_dict, sort_keys=True, indent=4)

    def __str__(self):
        return self.name


class VirshCmdResult(utils.CmdResult):
    @classmethod
    def from_result(cls, cmd, result):
        def sub(cmd, text):
            text = text.decode('utf-8')
            for opt in cmd.options:
                line = opt.line
                replacement = '${%s}' % opt.option.name
                if line and line in text:
                    text = text.replace(line, replacement)
            return text

        result.__class__ = cls
        result.cmdname = cmd.command.name

        result.sub_stdout = sub(cmd, result.stdout)
        result.sub_stderr = sub(cmd, result.stderr)

        result.key = '\n'.join((
            result.exit_status,
            result.sub_stdout,
            result.sub_stderr,
        ))
        return result


class RunnableCommand(object):

    def __init__(self):
        self.command = None
        self.options = []
        self.cmd_line = None

    @classmethod
    def random(cls, cmd_type):
        cmd = cls()
        cmd.command = cmd_type

        exc_opts = set()
        excs = []
        combs = []
        optionals = []
        requires = []
        if hasattr(cmd.command, 'exclusives'):
            excs = cmd.command.exclusives
            exc_opts = set(itertools.chain.from_iterable(excs))

        if hasattr(cmd.command, 'optionals'):
            optionals = cmd.command.optionals

        if hasattr(cmd.command, 'requires'):
            requires = cmd.command.requires

        cmd.options = []
        cmd.pre_funcs = []
        cmd.post_funcs = []
        for name, opt in cmd_type.options.items():
            if name not in exc_opts:
                required = None
                if name in optionals:
                    required = False
                if name in requires:
                    required = True

                rnd_opt = opt.random(force_required=required)
                cmd.pre_funcs.append(rnd_opt.pre)
                cmd.post_funcs.append(rnd_opt.post)
                cmd.options.append(rnd_opt)

        for comb_len in xrange(0, len(exc_opts)):
            for comb in itertools.combinations(exc_opts, comb_len):
                for exc_a, exc_b in excs:
                    if exc_a not in comb and exc_b not in comb:
                        combs.append(comb)

        if combs:
            for opt_name in random.choice(combs):
                opt = cmd_type.options[opt_name]
                cmd.options.append(opt.random(force_required=True))

        cmd.get_cmd_line()
        return cmd

    def get_cmd_line(self):
        if not self.cmd_line:
            cmd_line = 'virsh ' + self.command.name
            for option in self.options:
                if option.line is None:
                    continue
                else:
                    result_line = '--' + option.option.name
                    if option.line:
                        result_line += ' %s' % utils.escape(option.line)
                    cmd_line += ' %s' % result_line
            self.cmd_line = cmd_line
        return self.cmd_line

    def run(self, timeout=60):
        for func in self.pre_funcs:
            func()
        cmd_result = utils.run(self.cmd_line, timeout=timeout)
        for func in self.post_funcs:
            func()
        return VirshCmdResult.from_result(self, cmd_result)
