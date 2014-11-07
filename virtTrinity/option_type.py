import random
import random_lib


class OptionType(object):
    def __init__(self, type_name):
        self.type_name = type_name

    def parse_not_set(self):
        return None

    def parse_number(self):
        return str(random_lib.random_int())

    def parse_string(self):
        return random_lib.random_string()

    def parse_reboot_mode(self):
        return random.choice(
            ["acpi", "agent", "initctl", "signal", "paravirt"])

    def parse_fd(self):
        return random_lib.random_string()

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

    def parse_types(self):
        return [self.parse_type(name)
                for name in [self.type_name, 'not_set']]

    def random(self, required=False):
        opt_types = [self.type_name]
        if not required:
            opt_types.append('not_set')
        type_name = random.choice(opt_types)
        res = self.parse_type(type_name)
        return res
