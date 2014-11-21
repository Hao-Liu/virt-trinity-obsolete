import random
import random_lib


def parse_not_set():
    return None


def parse_number():
    return str(random_lib.random_int())


def parse_string():
    return random_lib.random_string()


def parse_reboot_mode():
    return random.choice(
        ["acpi", "agent", "initctl", "signal", "paravirt"])


def parse_fd():
    return random_lib.random_string()


def parse_pool():
    return 'virt-trinity-pool'


def parse_bool():
    return ''


def parse_domain():
    return 'virt-trinity-vm1'


def parse_file():
    return 'virt-trinity-file'


def parse_device_xml():
    return 'virt-trinity-device.xml'


def parse_type(type_name):
    return globals()['parse_' + type_name]()


def parse_types(type_name):
    return [parse_type(type_name)
            for name in [type_name, 'not_set']]


def select(type_name, required=False):
    opt_types = [type_name]
    if not required:
        opt_types.append('not_set')
    type_name = random.choice(opt_types)
    res = parse_type(type_name)
    return res
