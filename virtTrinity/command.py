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
        self.weight = 1.0

    def _parse_options(self):
        options = {}
        if self.options:
            last_name = ''
            for opt_line in self.options:
                opt = option.Option.from_help(
                    opt_line, self.name)
                if opt.opt_type == 'string' and opt.required:
                    if '[<%s>]' % opt.name in self.synopsis:
                        opt.required = False
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
                        if opt_name in cmd.options:
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

        result.__class__ = cls
        result.cmdname = cmd.command.name

        result.sub_stdout = result._sub(cmd, result.stdout)
        result.sub_stderr = result._sub(cmd, result.stderr)

        return result

    def _sub(self, cmd, text):
        text = text.decode('utf-8')

        found = False
        if hasattr(cmd.command, 'result_patterns'):
            for patt_str in cmd.command.result_patterns:
                param_strs = re.findall('\$\{(.*?)\}', patt_str)
                params = []
                for param_str in param_strs:
                    if ':' in param_str:
                        param_name, param_type = param_str.split(':', 1)
                    else:
                        param_name = param_str
                        param_type = 'all'
                    param_tpl = param_name.upper() + "PLACEHOLDER"
                    params.append((param_name, param_type,
                                   param_str, param_tpl))

                template = patt_str
                for param_name, param_type, param_str, param_tpl in params:
                    template = re.sub(
                        re.escape('${%s}' % param_str),
                        param_tpl,
                        template)

                regex = re.escape(template)
                for param_name, param_type, param_str, param_tpl in params:
                    if param_type == 'all':
                        param_re = r'.*'
                    elif param_type == 'int':
                        param_re = r'[-0-9]*'
                    else:
                        param_re = param_type

                    regex = re.sub(
                        param_tpl,
                        '(?P<%s>%s)' % (param_name, param_re),
                        regex)

                repl = template
                for param_name, param_type, param_str, param_tpl in params:
                    repl = re.sub(
                        param_tpl,
                        '${%s}' % param_name,
                        repl)

                match = re.search(regex, text)

                if match:
                    text = re.sub(regex, repl, text)
                    found = True

        if not found:
            for opt in cmd.options:
                line = opt.line
                replacement = '${%s}' % opt.option.name
                if line and line in text:
                    text = text.replace(line, replacement)
        return text


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
        optionals = []
        requires = []
        skips = []
        if hasattr(cmd.command, 'exclusives'):
            excs = cmd.command.exclusives
            exc_opts = set(opt for opt in itertools.chain.from_iterable(excs)
                           if opt in cmd.command.options)

        if hasattr(cmd.command, 'depends'):
            deps = cmd.command.depends

        if hasattr(cmd.command, 'optionals'):
            optionals = cmd.command.optionals

        if hasattr(cmd.command, 'requires'):
            requires = cmd.command.requires

        if hasattr(cmd.command, 'skips'):
            skips = cmd.command.skips

        cmd.options = []
        cmd.pre_funcs = []
        cmd.post_funcs = []
        cmd.opt_args = {}
        for name, opt in cmd_type.options.items():
            if name not in exc_opts:
                required = None
                if name in optionals:
                    required = False
                if name in requires:
                    required = True
                if name not in skips:
                    rnd_opt = opt.random(
                        cmd.opt_args,
                        force_required=required)
                    cmd.pre_funcs.append(rnd_opt.pre)
                    cmd.post_funcs.append(rnd_opt.post)
                    cmd.options.append(rnd_opt)

        combs = []
        for comb_len in xrange(0, len(exc_opts) + 1):
            for comb in itertools.combinations(exc_opts, comb_len):
                excl = False
                for exc_a, exc_b in excs:
                    if exc_a in comb and exc_b in comb:
                        excl = True
                        break
                if not excl:
                    combs.append(comb)

        if combs:
            for opt_name in random.choice(combs):
                opt = cmd_type.options[opt_name]
                cmd.options.append(opt.random(
                    cmd.opt_args,
                    force_required=True))

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
