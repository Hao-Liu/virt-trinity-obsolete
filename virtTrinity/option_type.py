import utils
import os
import errno
import random
import string
from xml.etree import ElementTree


class RandomOptionBase(object):
    def __init__(self, opt_args):
        self.line = None
        self.option = None

    def pre(self):
        pass

    def post(self):
        pass


class RandomNotSet(RandomOptionBase):
    pass


class RandomString(RandomOptionBase):
    def __init__(self, opt_args):
        self.line = random_string()


class RandomNumber(RandomString):
    def __init__(self, opt_args):
        self.line = str(random.randint(-2, 100))


class RandomRebootMode(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice([
            "acpi", "agent", "initctl", "signal", "paravirt"])


class RandomFd(RandomString):
    pass


class RandomPool(RandomString):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-pool-1'
        pool_names = []
        for line in utils.run('virsh -q pool-list --all').stdout.splitlines():
            name = line.strip().split()[0]
            if name.startswith('virt-trinity-pool-'):
                pool_names.append(name)

        if pool_names:
            self.line = random.choice(pool_names)


class RandomVol(RandomString):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-vol-1'
        pool_name = 'virt-trinity-pool-1'
        if 'pool' in opt_args:
            pool_name = opt_args['pool']
        vol_names = []
        for line in utils.run('virsh -q vol-list %s' %
                              pool_name).stdout.splitlines():
            name = line.strip().split()[0]
            if name.startswith('virt-trinity-vol-'):
                vol_names.append(name)

        if vol_names:
            self.line = random.choice(vol_names)


class RandomBool(RandomOptionBase):
    def __init__(self, opt_args):
        self.line = ''


class RandomDomain(RandomString):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-1'
        vm_names = [
            name for name in
            utils.run('virsh list --all --name').stdout.splitlines()
            if name.startswith('virt-trinity-')
        ]
        if vm_names:
            self.line = random.choice(vm_names)


class RandomFile(RandomString):
    def __init__(self, opt_args):
        self.path = 'virt-trinity-file'
        self.line = self.path
        self.content = ''

    def pre(self):
        with open(self.path, 'w') as xml_file:
            xml_file.write(self.content)

    def post(self):
        os.remove(self.path)


class RandomVmXml(RandomFile):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-vm.xml'
        self.path = self.line
        self.content = """
            <domain type='kvm'>
              <name>virt-trinity-%s</name>
              <memory>100000</memory>
              <os><type>hvm</type></os>
            </domain>""" % random.randint(1, 9)


class RandomDeviceXml(RandomFile):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-device.xml'
        self.path = self.line
        self.content = """
        <interface type='bridge'>
            <source bridge='virbr0'/>
        </interface>
        """


class RandomPoolXml(RandomFile):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-pool.xml'
        self.path = self.line
        self.number = random.randint(1, 9)
        self.content = """
        <pool type='dir'>
            <name>virt-trinity-pool-%s</name>
          <target>
              <path>/var/lib/virt-trinity/pools/%s</path>
          </target>
        </pool>
        """ % (self.number, self.number)
        opt_args['pool'] = 'virt-trinit-pool-%s' % self.number

    def pre(self):
        path = "/var/lib/virt-trinity/pools/%s" % self.number

        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

        with open(self.path, 'w') as xml_file:
            xml_file.write(self.content)


class RandomVolXml(RandomFile):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-vol.xml'
        self.path = self.line
        self.number = random.randint(1, 9)
        self.content = """
        <volume type='file'>
          <name>virt-trinity-vol-%s</name>
          <capacity unit='bytes'>1000</capacity>
          <target>
            <path>virt-trinity-vol-%s</path>
          </target>
        </volume>
        """ % (self.number, self.number)


class RandomExistingDeviceXml(RandomDeviceXml):
    def __init__(self, opt_args):
        self.path = 'virt-trinity-device.xml'
        self.line = self.path
        self.content = '<>'
        xml = utils.run('virsh dumpxml virt-trinity-vm1').stdout
        if xml.strip():
            root = ElementTree.fromstring(xml)
            iface_xmls = root.findall("./devices/interface")
            if iface_xmls:
                self.content = ElementTree.tostring(random.choice(iface_xmls))


def parse_type(type_name, opt_args):
    camel_name = ''.join([w.capitalize() for w in type_name.split('_')])
    return globals()['Random' + camel_name](opt_args)


def parse_types(type_name, opt_args={}):
    return [parse_type(type_name, opt_args)
            for name in [type_name, 'not_set']]


def select(option, opt_args, required=False):
    opt_types = [option.opt_type]
    if not required:
        opt_types.append('not_set')
    type_name = random.choice(opt_types)
    res = parse_type(type_name, opt_args)
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
