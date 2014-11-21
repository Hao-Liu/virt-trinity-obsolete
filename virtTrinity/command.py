import re
import json
import option
import subprocess
import pkg_resources


class Command(object):
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
