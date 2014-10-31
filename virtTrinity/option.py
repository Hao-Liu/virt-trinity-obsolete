import json
import option_type


class Option(object):

    def __init__(self, opt_line=''):
        self.required = False

        if opt_line:
            self.name, self.opt_type, self.desc = [
                i.strip() for i in opt_line.split(' ', 2)]

            if self.name == '<string>':
                # Special case for 'virsh echo'
                self.name = ''
                self.opt_type = 'string'
            else:
                if self.name.startswith('[') and self.name.endswith(']'):
                    self.name = self.name[1:-1]
                    self.required = True
                self.name = self.name[2:]

                if self.opt_type == '<string>':
                    if self.name == 'domain':
                        self.opt_type = 'domain'
                    elif self.name == 'pool':
                        self.opt_type = 'pool'
                    elif self.name == 'file':
                        self.opt_type = 'file'
                    else:
                        self.opt_type = 'string'
                elif self.opt_type == '<number>':
                    self.opt_type = 'number'
                else:
                    self.opt_type = 'bool'

            self.opt_type = option_type.OptionType(self.opt_type)

    def __str__(self):
        return self.name

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
        pass

    def random(self):
        opt_line = self.opt_type.random(required=self.required)
        if opt_line is None:
            return ''
        else:
            result_line = '--' + self.name
            if opt_line:
                result_line += ' %s' % opt_line
            return result_line

    def type_list(self):
        all_types = self.opt_type.parse_types(self.name)
        return all_types
