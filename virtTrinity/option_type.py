import utils
import os
import random
import string


class RandomOptionBase(object):
    def __init__(self):
        self.line = None
        self.option = None

    def pre(self):
        pass

    def post(self):
        pass


class RandomNotSet(RandomOptionBase):
    pass


class RandomString(RandomOptionBase):
    def __init__(self):
        self.line = random_string()


class RandomNumber(RandomString):
    def __init__(self):
        self.line = str(random.randint(-2, 100))


class RandomRebootMode(RandomString):
    def __init__(self):
        self.line = random.choice([
            "acpi", "agent", "initctl", "signal", "paravirt"])


class RandomFd(RandomString):
    pass


class RandomPool(RandomString):
    def __init__(self):
        self.line = 'virt-trinity-pool'


class RandomBool(RandomOptionBase):
    def __init__(self):
        self.line = ''


class RandomDomain(RandomString):
    def __init__(self):
        self.line = 'virt-trinity-vm1'


class RandomFile(RandomString):
    def __init__(self):
        self.line = 'virt-trinity-file'


class RandomDeviceXml(RandomFile):
    def __init__(self):
        self.line = 'virt-trinity-device.xml'

    def pre(self):
        xml_content = """
        <interface type='bridge'>
            <source bridge='virbr0'/>
        </interface>
        """
        with open('virt-trinity-device.xml', 'w') as xml_file:
            xml_file.write(xml_content)

    def post(self):
        os.remove('virt-trinity-device.xml')


def parse_type(type_name):
    camel_name = ''.join([w.capitalize() for w in type_name.split('_')])
    return globals()['Random' + camel_name]()


def parse_types(type_name):
    return [parse_type(type_name)
            for name in [type_name, 'not_set']]


def select(option, required=False):
    opt_types = [option.opt_type]
    if not required:
        opt_types.append('not_set')
    type_name = random.choice(opt_types)
    res = parse_type(type_name)
    res.option = option
    return res


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
