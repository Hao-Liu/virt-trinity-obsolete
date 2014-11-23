import utils
import random
import string


def random_not_set():
    return None


def random_number():
    return str(random.randint(-2, 100))


def random_string(escape=False, min_len=5, max_len=10):
    """
    Generate a randomized string.
    """

    excludes = "\n\t\r\x0b\x0c"

    chars = []
    for char in string.printable:
        if char not in excludes:
            chars.append(char)

    length = random.randint(min_len, max_len)

    result_str = ''.join(random.choice(chars) for _ in xrange(length))

    if escape:
        return utils.escape(result_str)
    else:
        return result_str


def random_reboot_mode():
    return random.choice(
        ["acpi", "agent", "initctl", "signal", "paravirt"])


def random_fd():
    return random_string()


def random_pool():
    return 'virt-trinity-pool'


def random_bool():
    return ''


def random_domain():
    return 'virt-trinity-vm1'


def random_file():
    return 'virt-trinity-file'


def random_device_xml():
    return 'virt-trinity-device.xml'


def parse_type(type_name):
    return globals()['random_' + type_name]()


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
