import random
import random_lib


class OptionType(object):
    all_types = {
        'number': [
            'number',
            'not_set',
        ],
        'bool': [
            'bool',
            'not_set',
        ],
        'string': [
            'string',
            'not_set',
        ],
        'domain': [
            'domain',
            'not_set',
        ],
        'pool': [
            'pool',
            'not_set',
        ],
        'file': [
            'file',
            'not_set',
        ],
        'device_xml': [
            'device_xml',
            'not_set',
        ],
    }

    def __init__(self, type_name):
        self.type_name = type_name
        self.opt_types = self.all_types[type_name]

    def parse_not_set(self):
        return None

    def parse_number(self):
        return random_lib.random_int()

    def parse_string(self):
        return random_lib.random_string(escape=True)

    def parse_pool(self):
        return 'virt-trinity-pool'

    def parse_bool(self):
        return ''

    def parse_domain(self):
        return 'virt-trinity-vm1'

    def parse_file(self):
        return 'virt-trinity-file'

    def parse_device_xml(self):
        return 'virt-trinity-device.xml'

    def parse_type(self, type_name):
        parse_fun = getattr(self, 'parse_' + type_name)
        return parse_fun()

    def parse_types(self, opt_name):
        parsed_types = []
        for opt_type in self.opt_types:
            parse_fun = getattr(self, 'parse_' + opt_type)
            parsed_types.append(parse_fun())
        return parsed_types

    def random(self, required=False):
        opt_types = self.opt_types[:]
        if required:
            opt_types.remove('not_set')
        type_name = random.choice(opt_types)
        res = self.parse_type(type_name)
        return res
