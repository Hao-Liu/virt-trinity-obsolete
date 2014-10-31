import re
import json
import option
import subprocess


class Command(object):
    name = ''
    options = []

    def __init__(self, name=''):
        if name:
            self.name = name
            self.synopsis = ''
            self.load_from_help(name)

    def load_from_help(self, name):
        self.short_name = name
        help_txt = subprocess.check_output(
            ['virsh', 'help', name]).splitlines()

        item_name = ''
        item_content = []
        for line in help_txt:
            if re.match(r'^  [A-Z]*$', line):
                if item_name:
                    if item_name == 'options':
                        setattr(self, item_name, item_content)
                    else:
                        setattr(self, item_name, ''.join(item_content))
                    item_content = []
                item_name = line.strip().lower()
            else:
                if line:
                    item_content.append(line.strip())
        if item_name:
            if item_name == 'options':
                setattr(self, item_name, item_content)
            else:
                setattr(self, item_name, ''.join(item_content))
            item_content = []

        assert name == self.name.split()[0]
        assert self.synopsis
        self.parse_options()

    def parse_options(self):
        options = []
        if self.options:
            for opt_line in self.options:
                options.append(option.Option(opt_line, command=self))
        if '...' in self.synopsis:
            options[-1].argv = True
        self.options = options

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        cmd = cls()
        for key in json_dict:
            value = json_dict[key]
            if key == 'options':
                options = []
                for opt_dict in json_dict[key]:
                    opt_json = json.dumps(opt_dict)
                    opt = option.Option.from_json(opt_json)
                    options.append(opt)
                value = options
            setattr(cmd, key, value)
        return cmd

    def to_json(self):
        json_dict = {}
        for key in self.__dict__:
            value = getattr(self, key)
            if key == 'options':
                value = []
                for option in self.options:
                    value.append(json.loads(option.to_json()))
            json_dict[key] = value

        return json.dumps(json_dict, sort_keys=True, indent=4)

    def __str__(self):
        return self.short_name
