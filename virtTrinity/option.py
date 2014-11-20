import json
import option_type
import pkg_resources


class Option(object):
    specified_opt_types = json.loads(
            pkg_resources.resource_string(
                __name__, 'data/virsh_option_types.json'))

    def _parse_help(self, help_line):
        cmd_name = self.cmd_name
        name, type_name, self.desc = [
            i.strip() for i in help_line.split(' ', 2)]

        if name.startswith('[') and name.endswith(']'):
            name = name[1:-1]
            self.required = True

        if name.startswith('<') and name.endswith('>'):
            if name == '<string>':
                # Special case for 'virsh echo'
                name = ''
                type_name = 'string'
            else:
                name = name[1:-1]

        if name.startswith('--'):
            name = name[2:]

        self.name = name

        types = Option.specified_type_names
        if cmd_name in types and name in types[cmd_name]:
            self.type_name = types[cmd_name][name]
        else:
            if type_name == '<string>':
                known_types = ['domain', 'pool', 'file']
                if name in known_types:
                    type_name = name
                else:
                    type_name = 'string'
            elif type_name == '<number>':
                type_name = 'number'
            else:
                type_name = 'bool'
        self.opt_type = option_type.OptionType(type_name)

    def __str__(self):
        return self.name

    @classmethod
    def from_help(cls, opt_line, cmd_name):
        option = cls()
        option.required = False
        option.cmd_name = cmd_name
        option._parse_help(opt_line)

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        option = cls()
        for key in json_dict:
            value = json_dict[key]
            if key == 'opt_type':
                value = option_type.OptionType(value)
            setattr(option, key, value)
        return option

    def to_json(self):
        json_dict = {}
        for key in self.__dict__:
            value = getattr(self, key)
            if key == 'opt_type':
                value = self.opt_type.type_name
            json_dict[key] = value

        return json.dumps(json_dict, sort_keys=True, indent=4)

    def random(self):
        return self.opt_type.random(required=self.required)

    def type_list(self):
        all_types = self.opt_type.parse_types()
        return all_types
