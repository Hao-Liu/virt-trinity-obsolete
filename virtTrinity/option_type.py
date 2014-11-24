import utils
import os
import random
import string
from xml.etree import ElementTree


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
        vm_names = [
            name for name in
            utils.run('virsh list --all --name').stdout.splitlines()
            if name.startswith('virt-trinity-')
        ]
        if vm_names:
            self.line = random.choice(vm_names)


class RandomFile(RandomString):
    def __init__(self):
        self.path = 'virt-trinity-file'
        self.line = self.path
        self.content = ''

    def pre(self):
        with open(self.path, 'w') as xml_file:
            xml_file.write(self.content)

    def post(self):
        os.remove(self.path)


class RandomVmXml(RandomFile):
    def __init__(self):
        self.line = 'virt-trinity-vm.xml'
        self.path = self.line
        self.content = """
            <domain type='kvm'>
              <name>virt-trinity-%s</name>
              <memory>100000</memory>
              <os><type>hvm</type></os>
            </domain>""" % random.randint(1, 9)


class RandomDeviceXml(RandomFile):
    def __init__(self):
        self.line = 'virt-trinity-device.xml'
        self.path = self.line
        self.content = """
        <interface type='bridge'>
            <source bridge='virbr0'/>
        </interface>
        """


class RandomExistingDeviceXml(RandomDeviceXml):
    def __init__(self):
        self.path = 'virt-trinity-device.xml'
        self.line = self.path
        self.content = '<>'
        xml = utils.run('virsh dumpxml virt-trinity-vm1').stdout
        if xml.strip():
            root = ElementTree.fromstring(xml)
            iface_xmls = root.findall("./devices/interface")
            if iface_xmls:
                self.content = ElementTree.tostring(random.choice(iface_xmls))


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
