import utils
import os
import errno
import random
import string
import utils_random
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


class RandomNonNegative(RandomNumber):
    def __init__(self, opt_args):
        self.line = str(random.randint(0, 100))


class RandomHugePageSize(RandomNumber):
    def __init__(self, opt_args):
        self.line = "2048"


class RandomCellNumber(RandomNumber):
    def __init__(self, opt_args):
        self.line = "0"


class RandomRebootMode(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice([
            "acpi", "agent", "initctl", "signal", "paravirt"])


class RandomFd(RandomNumber):
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
            opt_args['domain'] = self.line
        else:
            opt_args['skip'] = True


class RandomActiveDomain(RandomDomain):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-1'
        vm_names = [
            name for name in
            utils.run('virsh list --name').stdout.splitlines()
            if name.startswith('virt-trinity-')
        ]
        if vm_names:
            self.line = random.choice(vm_names)
            opt_args['domain'] = self.line
        else:
            opt_args['skip'] = True


class RandomInactiveDomain(RandomDomain):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-1'
        vm_names = [
            name for name in
            utils.run('virsh list --inactive --name').stdout.splitlines()
            if name.startswith('virt-trinity-')
        ]
        if vm_names:
            self.line = random.choice(vm_names)
            opt_args['domain'] = self.line
        else:
            opt_args['skip'] = True


class RandomUnexistDomain(RandomDomain):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-1'
        all_names = ['virt-trinity-' + str(i) for i in xrange(1, 10)]
        vm_names = [
            name for name in
            utils.run('virsh list --all --name').stdout.splitlines()
            if name.startswith('virt-trinity-')
        ]
        avail_names = list(set(all_names) - set(vm_names))
        if avail_names:
            self.line = random.choice(avail_names)
            opt_args['domain'] = self.line
        else:
            opt_args['skip'] = True


class RandomFile(RandomString):
    def __init__(self, opt_args):
        self.path = 'virt-trinity-file'
        self.line = self.path
        self.content = ''

    def pre(self):
        with open(self.path, 'w') as xml_file:
            xml_file.write(self.content)

    def post(self):
        if os.path.exists(self.path):
            os.remove(self.path)


class RandomPermanentFile(RandomFile):
    def __init__(self, opt_args):
        self.path = '/tmp/virt-trinity-file'
        self.line = self.path
        self.content = ''

    def post(self):
        pass

class RandomWord(RandomString):
    def __init__(self, opt_args):
        # Should be looser
        chars = string.ascii_letters + string.digits
        length = random.randint(5, 10)
        self.line = ''.join(random.choice(chars) for _ in xrange(length))


class RandomXmlString(RandomString):
    def __init__(self, opt_args):
        # Should be looser
        chars = string.ascii_letters + string.digits + '_-+.'
        length = random.randint(5, 10)
        self.line = ''.join(random.choice(chars) for _ in xrange(length))


class RandomVmXml(RandomFile):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-vm.xml'
        self.path = self.line

        vm_name = 'virt-trinity-1'
        all_names = ['virt-trinity-' + str(i) for i in xrange(1, 10)]
        vm_names = [
            name for name in
            utils.run('virsh list --all --name').stdout.splitlines()
            if name.startswith('virt-trinity-')
        ]
        avail_names = list(set(all_names) - set(vm_names))
        if avail_names:
            vm_name = random.choice(avail_names)
            self.content = utils_random.xml('domain', name=vm_name)
        else:
            opt_args['skip'] = True


class RandomDeviceXml(RandomFile):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-device.xml'
        self.path = self.line
        self.content = utils_random.device_xml()


class RandomPoolXml(RandomFile):
    def __init__(self, opt_args):
        self.line = 'virt-trinity-pool.xml'
        self.path = self.line
        self.number = random.randint(1, 9)
        name = 'virt-trinity-pool-%s' % self.number
        self.content = utils_random.xml('storagepool', name=name)
        opt_args['pool'] = name

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
        name = 'virt-trinity-vol-%s' % self.number
        self.content = utils_random.xml('storagevol', name=name)


class RandomExistDisk(RandomString):
    def __init__(self, opt_args):
        self.line = "disk-not-found"
        if 'domain' in opt_args:
            text = utils.run(
                'virsh -q domblklist %s' % opt_args['domain']).stdout
            disks = [l.split()[0] for l in text.strip().splitlines()]
            if disks:
                self.line = random.choice(disks)


class RandomDiskCountString(RandomString):
    def __init__(self, opt_args):
        self.line = "vda,1"
        if 'domain' in opt_args:
            text = utils.run(
                'virsh -q domblklist %s' % opt_args['domain']).stdout
            disks = [l.split()[0] for l in text.strip().splitlines()]
            if disks:
                disk_strs = []
                for disk in disks:
                    disk_strs.append(disk)
                    disk_strs.append(str(random.randint(-2, 100)))
                if disk_strs:
                    self.line = ",".join(disk_strs)
                else:
                    opt_args['skip'] = True
            else:
                opt_args['skip'] = True
        else:
            opt_args['skip'] = True


class RandomDiskSourceType(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['file', 'block'])


class RandomDiskAddress(RandomString):
    def __init__(self, opt_args):
        bus_type = random.choice(['pci', 'scsi', 'ide'])
        n = 3
        if bus_type == 'pci':
            n = 4
        addr_list = [str(random.randint(1, 9)) for i in xrange(n)]
        self.line = '%s:%s' % (bus_type, '.'.join(addr_list))


class RandomDiskType(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['lun', 'cdrom', 'floppy'])


class RandomDiskSerial(RandomString):
    def __init__(self, opt_args):
        chars = string.ascii_letters + string.digits + '_-+.'
        length = random.randint(5, 10)
        self.line = ''.join(random.choice(chars) for _ in xrange(length))


class RandomDiskName(RandomString):
    def __init__(self, opt_args):
        prefix = random.choice(['hd', 'sd', 'vd', 'xvd', 'ubd'])
        postfix = random.choice(string.ascii_letters)
        self.line = prefix + postfix


class RandomDiskBus(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['ide', 'scsi', 'virtio', 'xen', 'usb',
                                   'sata', 'sd'])


class RandomDiskDriver(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['file', 'tap', 'phy', 'qemu'])


class RandomDiskSubDriver(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['aio', 'raw', 'qcow2'])


class RandomDiskIothread(RandomNumber):
    pass


class RandomDiskCache(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['default', 'none', 'writethrough',
                                   'writeback', 'directsync', 'unsafe'])


class RandomDiskMode(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['readonly', 'shareable'])


class RandomWwn(RandomNumber):
    def __init__(self, opt_args):
        self.line = ''.join([str(random.choice(string.hexdigits))
                             for i in xrange(16)])


class RandomIfaceType(RandomString):
    def __init__(self, opt_args):
        self.line = random.choice(['network', 'bridge'])
        opt_args['iface-type'] = self.line


class RandomIfaceRate(RandomString):
    def __init__(self, opt_args):
        average = str(random.randint(-2, 100))
        peak = random.choice([str(random.randint(-2, 100)), ''])
        burst = random.choice([str(random.randint(-2, 100)), ''])
        if burst == '':
            if peak:
                self.line = ','.join((average, peak))
            else:
                self.line = average
        else:
            self.line = ','.join((average, peak, burst))


class RandomMac(RandomString):
    def __init__(self, opt_args):
        mac = ["%02x" % random.randint(0x00, 0xff)
               for i in xrange(6)]
        self.line = ':'.join(mac)


class RandomUnicastMac(RandomString):
    def __init__(self, opt_args):
        mac = ["%02x" % random.randint(0x00, 0xff)
               for i in xrange(6)]
        mac[0] = "%02x" % (random.randint(0x00, 0xff) / 2 * 2)
        self.line = ':'.join(mac)


class RandomIfaceSource(RandomString):
    def __init__(self, opt_args):
        self.line = 'net-not-found'
        text = utils.run('virsh -q net-list').stdout
        nets = [l.split()[0] for l in text.strip().splitlines()]
        text = utils.run('brctl show').stdout
        brs = [l.split()[0]
               for l in text.strip().splitlines()[1:]
               if l[0] not in string.whitespace]
        if 'iface-type' in opt_args:
            iface_type = opt_args['iface-type']
            if iface_type == 'network':
                if nets:
                    self.line = random.choice(nets)
            elif iface_type == 'bridge':
                if brs:
                    self.line = random.choice(brs)
        else:
            self.line = random.choice(nets + brs)


class RandomStorageFormat(RandomString):
    def __init__(self, opt_args):
        formats = ["none", "raw", "dir", "bochs", "cloop", "dmg", "iso",
                   "vpc", "vdi", "fat", "vhd", "ploop", "cow", "qcow",
                   "qcow2", "qed", "vmdk"]
        self.line = random.choice(formats)


class RandomExistDeviceXml(RandomDeviceXml):
    def __init__(self, opt_args):
        self.path = 'virt-trinity-device.xml'
        self.line = self.path
        self.content = '<>'
        if 'domain' in opt_args:
            xml = utils.run('virsh dumpxml %s' % opt_args['domain']).stdout
            if xml.strip():
                root = ElementTree.fromstring(xml)
                iface_xmls = root.findall("./devices/interface")
                if iface_xmls:
                    self.content = ElementTree.tostring(
                        random.choice(iface_xmls))
                else:
                    opt_args['skip'] = True
        else:
            opt_args['skip'] = True


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
