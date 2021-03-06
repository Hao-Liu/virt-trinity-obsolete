import json
import option_type


class Option(object):
    def _parse_help(self, help_line):
        name, type_name, self.desc = [
            i.strip() for i in help_line.split(' ', 2)]

        if name.startswith('[') and name.endswith(']'):
            name = name[1:-1]
            self.required = True

        if name.startswith('<') and name.endswith('>'):
            if name == '<string>':
                # Special case for 'virsh echo'
                name = ''
                type_name = '<string>'
            else:
                name = name[1:-1]

        if name.startswith('--'):
            name = name[2:]

        self.name = name

        if type_name == '<string>':
            known_types = ['domain', 'pool', 'file', 'vol']
            if name in known_types:
                type_name = name
            else:
                type_name = 'string'
        elif type_name == '<number>':
            type_name = 'number'
        else:
            type_name = 'bool'
        self.opt_type = type_name

    def __str__(self):
        return self.name

    @classmethod
    def from_help(cls, opt_line, cmd_name):
        option = cls()
        option.required = False
        option.cmd_name = cmd_name
        option._parse_help(opt_line)
        return option

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        option = cls()
        for key in json_dict:
            value = json_dict[key]
            setattr(option, key, value)
        return option

    def to_json(self):
        json_dict = {}
        for key in self.__dict__:
            value = getattr(self, key)
            json_dict[key] = value
        return json.dumps(json_dict, sort_keys=True, indent=4)

    def random(self, opt_args, force_required=None):
        required = self.required
        if force_required is not None:
            required = bool(force_required)
        return option_type.select(self, opt_args, required=required)

    def type_list(self):
        all_types = option_type.parse_types(self.opt_type)
        return all_types
