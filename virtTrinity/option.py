import option_type


class Option(object):
    required = False

    def __init__(self, opt_line=''):
        if opt_line:
            self.name, self.type, self.desc = [
                i.strip() for i in opt_line.split(' ', 2)]

            if self.name == '<string>':
                # Special case for 'virsh echo'
                self.name = ''
                self.type = 'string'
            else:
                if self.name.startswith('[') and self.name.endswith(']'):
                    self.name = self.name[1:-1]
                    self.required = True
                self.name = self.name[2:]

                if self.type == '<string>':
                    self.type = 'string'
                elif self.type == '<number>':
                    self.type = 'number'
                else:
                    self.type = 'bool'

    def __str__(self):
        return self.name

    def get_domain_name(self):
        return 'virt-fsm-vm1'

    def type_list(self):
        if self.type == 'bool':
            opt_type = 'bool'
        if self.type == 'string':
            if self.name == 'domain':
                opt_type = 'domain'
            else:
                opt_type = 'string'
        all_types = option_type.OptionType(opt_type).parse_types(self.name)
        return all_types
