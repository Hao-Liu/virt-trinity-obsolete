import random
import utils_random
import xml_gen

UNIT_MAP = {
    "b": 1,
    "byte": 1,
    "k": 1000**1,
    "m": 1000**2,
    "g": 1000**3,
    "t": 1000**4,
    "p": 1000**5,
    "e": 1000**6,
    "kb": 1000**1,
    "mb": 1000**2,
    "gb": 1000**3,
    "tb": 1000**4,
    "pb": 1000**5,
    "eb": 1000**6,
    "kib": 1024**1,
    "mib": 1024**2,
    "gib": 1024**3,
    "tib": 1024**4,
    "pib": 1024**5,
    "eib": 1024**6,
}

def cpuset(node, param, xml):
    if xml.node_str == 'data /domain/cpu/numa/cell':
        return '0'
    return '0-2,^1'

def dec(node, param, xml):
    max_val = int(param)
    n = utils_random.integer(0, max_val)
    return str(n)

def integer(node, param, xml):
    if ' ' in param:
        min_val, max_val = [int(v) for v in param.split()]
    else:
        min_val = 0
        max_val = int(param)
    n = utils_random.integer(min_val, max_val)
    return str(n)

def hexdec(node, param, xml):
    if ' ' in param:
        min_val, max_val = [int(v) for v in param.split()]
    else:
        min_val = 0
        max_val = int(param)
    n = utils_random.integer(min_val, max_val)
    s = random.choice([str(n), hex(n)])
    return s

def pcifunc(node, param, xml):
    n = utils_random.integer(0, 7)
    s = random.choice([str(n), hex(n)])
    return s

def usbport(node, param, xml):
    max_val = int(param)
    cnt = utils_random.integer(1, 4)
    return '.'.join([str(utils_random.integer(0, max_val)) for i in xrange(cnt)])

def max_vcpu(node, param, xml):
    return str(get_maxvcpu(xml))



def get_maxvcpu(xml):
    if 'maxvcpu' in xml.params:
        cnt = xml.params['maxvcpu']
    else:
        cnt = xml.params['maxvcpu'] = utils_random.integer(1, 5)
    return cnt

def metadata(xml, node):
    pass

def domain_type(xml, node):
    t = random.choice(["qemu", "kvm", "xen"])
    xml.cur_xml.set(node.get('name'), t)

def current_vcpu(xml, node):
    maxvcpu = get_maxvcpu(xml)
    cnt = utils_random.integer(1, maxvcpu)
    xml.cur_xml.set(node.get('name'), str(cnt))

def vcpupin(xml, node):
    if node.find('./element[@name="vcpupin"]') is not None:
        maxvcpu = get_maxvcpu(xml)
        child = list(node)[0]
        cnt = utils_random.integer(0, maxvcpu)
        for i in xrange(cnt):
            xml.parse_node(child)
    else:
        return True

def idmap(xml, node):
    if node.find('./element[@name="gid"]') is not None:
        if xml.xml.find('./idmap/uid') is not None:
            maxvcpu = get_maxvcpu(xml)
            child = list(node)[0]
            cnt = utils_random.integer(1, maxvcpu)
            for i in xrange(cnt):
                xml.parse_node(child)
    else:
        return True

def dev_source(xml, node):
    if node.find('./element[@name="source"]') is not None:
        if xml.cur_xml.get('type') in ['dev', 'file', 'unix', 'pipe', 'udp', 'tcp', 'spiceport']:
            child = list(node)[0]
            cnt = int(random.expovariate(0.5)) + 1
            for i in xrange(cnt):
                xml.parse_node(child)
        else:
            return True
    else:
        return True

def vcpupin_cpu(xml, node):
    maxvcpu = get_maxvcpu(xml)
    if 'unpined_cpus' in xml.params:
        unpined_cpus = xml.params['unpined_cpus']
    else:
        unpined_cpus = xml.params['unpined_cpus'] = set(xrange(maxvcpu))
    cpuid = random.choice(list(unpined_cpus))
    xml.params['unpined_cpus'].remove(cpuid)
    xml.cur_xml.set(node.get('name'), str(cpuid)) 

def numa_id(xml, node):
    if 'numa_maxid' not in xml.params:
        xml.params['numa_maxid'] = 0
    else:
        xml.params['numa_maxid'] += 1
    n = xml.params['numa_maxid']
    xml.cur_xml.set(node.get('name'), str(n)) 

def numa_cnt(xml, node):
    maxvcpu = get_maxvcpu(xml)
    child = list(node)[0]
    cnt = utils_random.integer(1, maxvcpu)
    for i in xrange(cnt):
        xml.parse_node(child)

def max_mem(xml, node):
    data = str(xml.params['maxmem'] / UNIT_MAP[xml.params['maxmem_unit']])
    if xml.temp_value:
        xml.temp_value = data
    else:
        if xml.cur_xml.text is None:
            xml.cur_xml.text = data
        else:
            xml.cur_xml.text += data

def max_mem_unit(xml, node):
    maxmem = utils_random.integer(1, 10000000)
    unit = 'eib'
    while maxmem <= UNIT_MAP[unit]:
        unit = random.choice(UNIT_MAP.keys())
    maxmem /= UNIT_MAP[unit]
    maxmem *= UNIT_MAP[unit]
    xml.params['maxmem'] = maxmem
    xml.params['maxmem_unit'] = unit
    xml.cur_xml.set(node.get('name'), str(unit))

def cur_mem(xml, node):
    data = str(xml.params['curmem'] / UNIT_MAP[xml.params['curmem_unit']])
    if xml.temp_value:
        xml.temp_value = data
    else:
        if xml.cur_xml.text is None:
            xml.cur_xml.text = data
        else:
            xml.cur_xml.text += data

def cur_mem_unit(xml, node):
    maxmem = xml.params['maxmem']
    curmem = utils_random.integer(1, maxmem)
    unit = 'eib'
    while curmem <= UNIT_MAP[unit]:
        unit = random.choice(UNIT_MAP.keys())
    curmem /= UNIT_MAP[unit]
    curmem *= UNIT_MAP[unit]
    xml.params['curmem'] = curmem
    xml.params['curmem_unit'] = unit
    xml.cur_xml.set(node.get('name'), str(unit)) 

def numatune_memnode(xml, node):
    placement = xml.xml.find('./numatune/memory').get('placement')
    if placement == 'strict':
        return True

def numatune_cellid(xml, node):
    n = utils_random.integer(0, xml.params['numa_maxid'])
    xml.cur_xml.set(node.get('name'), str(n)) 

def iothreads(xml, node):
    xml.params['iothreads'] = utils_random.integer(1, 10000000)
    data = str(xml.params['iothreads'])
    if xml.temp_value:
        xml.temp_value = data
    else:
        if xml.cur_xml.text is None:
            xml.cur_xml.text = data
        else:
            xml.cur_xml.text += data

def iothreadpin_iothread(xml, node):
    iothreads = xml.params['iothreads']
    iothread = utils_random.integer(0, iothreads)
    xml.cur_xml.set(node.get('name'), str(iothread)) 

def hyperv_spinlock_retries(xml, node):
    retries = utils_random.integer(4095, 100000000)
    xml.cur_xml.set(node.get('name'), str(retries)) 

def idmap_root(xml, node):
    root = 0
    xml.cur_xml.set(node.get('name'), str(root))

def source_mode(xml, node):
    if xml.xml_stack[-2].get('type') not in ['udp', 'tcp']:
        return True

    mode = random.choice(['connect', 'bind', None])
    if mode is not None:
        xml.cur_xml.set(node.get('name'), mode)

def vlan_native(xml, node):
    if xml.xml_stack[-2].find('./tag[@nativeMode]') is None:
        return True

def hostdev_startpol(xml, node):
    if xml.xml_stack[-2].get('type') == 'usb':
        return True


def hostdev_device(xml, node):
    # TODO: There should be a bug
    dev = utils_random.integer(0, 99999)
    xml.cur_xml.set(node.get('name'), str(dev))

def listen_address(xml, node):
    listen = xml.xml_stack[-2].get('listen')
    if listen is None:
        return True
    xml.cur_xml.set(node.get('name'), listen)

def iface_model(xml, node):
    iface_type = xml.xml_stack[-2].get('type')
    if iface_type != 'vhostuser':
        return True

    xml.cur_xml.set(node.get('name'), 'virtio')

def disk_target(xml, node):
    device = xml.xml_stack[-2].get('device')
    if device == 'floppy':
        data = utils_random.regex(r'(ioemu:)?fd[a-zA-Z0-9_]+')
    elif device in ['lun', 'disk']:
        data = utils_random.regex(r'(ioemu:)?(hd|sd|vd|xvd|ubd)[a-zA-Z0-9_]+')
    else:
        return True

    if xml.temp_value:
        xml.temp_value = data
    else:
        if xml.cur_xml.text is None:
            xml.cur_xml.text = data
        else:
            xml.cur_xml.text += data

def cpu_model_text(xml, node):
    data = xml.params['cpumodel'] = utils_random.text()
    if xml.temp_value:
        xml.temp_value = data
    else:
        if xml.cur_xml.text is None:
            xml.cur_xml.text = data
        else:
            xml.cur_xml.text += data

def cpu_model_empty(xml, node):
    xml.params['cpumodel'] = ""

def cpu_vendor(xml, node):
    if xml.params['cpumodel']:
        return True

def cpu_feature(xml, node):
    if xml.params['cpumodel']:
        return True

def device_boot(xml, node):
    if xml.xml.find('./os/boot') is None:
        return True

def sysinfo_entry(xml, node):
    name = xml.cur_xml.get('name')
    if name not in ['date', 'uuid']:
        return True
    if name == 'date':
        data = "01/01/1970"
    elif name == 'uuid':
        data = xml.xml.find('./uuid').text
    if xml.temp_value:
        xml.temp_value = data
    else:
        if xml.cur_xml.text is None:
            xml.cur_xml.text = data
        else:
            xml.cur_xml.text += data

def redirdev_address(xml, node):
    choices = []
    for addr in node.getchildren():
        add_type = addr.find('./attribute/value').text
        if add_type == 'usb':
            choices.append(addr)
    choice = random.choice(choices)
    xml.parse_node(choice)

def input_address(xml, node):
    if xml.xml_stack[-2].get('bus') != 'usb':
        return True

    for addr in node.getchildren():
        add_type = addr.find('./attribute/value').text
        if add_type == 'usb':
            choice = addr
    xml.parse_node(choice)

def pci_address(xml, node):
    if node.find('./group/attribute/value') is None:
        return True

    for addr in node.getchildren():
        add_type = addr.find('./attribute/value').text
        if add_type == 'pci':
            choice = addr
    xml.parse_node(choice)

def controller_model(xml, node):
    value = node.find('./value')
    if value is None:
        return True

    if value.text != 'pci-root':
        return True


    addr = xml.cur_xml.find('./address')
    xml.cur_xml.remove(addr)
    xml.cur_xml.set('index', '0')

    expect_type = None
    choices = []
    if xml.xml.find("./devices//address[@type='pci']") is not None:
        expect_type = 'pci-root'
    if xml.xml.find("./devices/controller[@model='dmi-to-pci-bridge']") is not None:
        expect_type = 'pcie-root'

    for val in node.getchildren():
        if expect_type is None:
            choices.append(val)
        else:
            if val.text == expect_type:
                choices.append(val)
                break
    choice = random.choice(choices)
    xml.parse_node(choice)

def serial_address(xml, node):
    if node.find('./group/attribute/value') is None:
        return True

    if xml.xml_stack[-2].find('./target[@type="usb-serial"]') is None:
        return True

    for addr in node.getchildren():
        add_type = addr.find('./attribute/value').text
        if add_type == 'usb':
            choice = addr
    xml.parse_node(choice)

def disk_address(xml, node):
    if node.find('./group/attribute/value') is None:
        return True

    if xml.xml_stack[-2].find('./target[@bus="virtio"]') is None:
        return True

    for addr in node.getchildren():
        add_type = addr.find('./attribute/value').text
        if add_type == 'pci':
            choice = addr
    xml.parse_node(choice)

def hostdev_address(xml, node):
    if node.find('./group/attribute/value') is None:
        return True

    if xml.xml_stack[-2].get('type') != 'pci':
        return True

    for addr in node.getchildren():
        add_type = addr.find('./attribute/value').text
        if add_type == 'pci':
            choice = addr
    xml.parse_node(choice)

def char_target(xml, node):
    if node.find('./optional/ref[@name="qemucdevConsoleTgtType"]') is None:
        return True
    tag = xml.xml_stack[-2].tag
    if tag == 'serial':
        choice = node.find('./optional/ref[@name="qemucdevSerialTgtType"]/..')
    elif tag == 'console':
        choice = node.find('./optional/ref[@name="qemucdevConsoleTgtType"]/..')
    else:
        return True
    xml.parse_node(choice)

def channel_target(xml, node):
    if node.find('./ref[@name="virtioTarget"]') is None:
        return True
    channel_type = xml.cur_xml.get('type')
    if channel_type != 'spicevmc':
        return True

    choice = node.find('./ref[@name="virtioTarget"]')
    xml.parse_node(choice)

def char_type(xml, node):
    if len(node.findall('./value')) < 10:
        return True

    choices = []
    for val in node.getchildren():
        if val.text != 'spicevmc':
            choices.append(val)
    choice = random.choice(choices)
    xml.parse_node(choice)

def input_bus(xml, node):
    value = node.find('./value')
    if value is None:
        return True
    if value.text != 'ps2':
        return True

    if xml.cur_xml.get('type') != 'tablet':
        return True

    choices = []
    for val in node.getchildren():
        if val.text != 'ps2':
            choices.append(val)
    choice = random.choice(choices)
    xml.parse_node(choice)

def disk_source(xml, node):
    if xml.xml_stack[-2].get('type') in ['floppy', 'cdrom']:
        return True

    choices = []
    for val in node.getchildren():
        if val.text != 'requisite':
            choices.append(val)
    choice = random.choice(choices)
    xml.parse_node(choice)

def hostdev_mode(xml, node):
    if xml.xml.get('type') not in ['qemu', 'xen', 'kvm']:
        return True

    if node.find('./group/ref[@name="hostdevcaps"]') is None:
        return True

    choices = []
    for mode in node.getchildren():
        mode_type = mode.find('./ref').get('name')
        if mode_type != 'hostdevcaps':
            choices.append(mode)
    choice = random.choice(choices)
    xml.parse_node(choice)

def listen_type(xml, node):
    if node.find('./group/attribute[@name="type"]/value') is None:
        return True

    if xml.xml_stack[-2].get('listen') is None:
        return True

    if len(xml.xml_stack[-2].findall('./listen')) > 1:
        return True

    choices = []
    for listen_type in node.getchildren():
        type_name = listen_type.find('./attribute[@name="type"]/value').text
        if type_name == 'address':
            choices.append(listen_type)
    choice = random.choice(choices)
    xml.parse_node(choice)

def seclabel(xml, node):
    labels = xml.xml.findall('./devices//seclabel')
    if not len(labels):
        return True

    choices = []
    for label_type in node.getchildren():
        type_name_xml = label_type.find(".//attribute[@name='type']/value")
        if type_name_xml is None:
            if label_type.text == 'no':
                continue
        else:
            type_name = type_name_xml.text
            if type_name == 'none':
                continue

        choices.append(label_type)
    choice = random.choice(choices)
    xml.parse_node(choice)

def qemu_path(xml, node):
    data = '/usr/bin/qemu-kvm'
    if xml.temp_value:
        xml.temp_value = data
    else:
        if xml.cur_xml.text is None:
            xml.cur_xml.text = data
        else:
            xml.cur_xml.text += data

def hugepage_nodeset(xml, node):
    if 'hugecpus' in xml.params:
        hugecpus = xml.params['hugecpus']
    else:
        hugecpus = xml.params['hugecpus'] = []

    cpu = int(random.expovariate(1))
    while cpu in hugecpus:
        cpu = int(random.expovariate(1))

    hugecpus.append(cpu)
    xml.cur_xml.set(node.get('name'), str(cpu)) 

def hugepage_size(xml, node):
    size = int(random.expovariate(0.1)) + 1
    xml.cur_xml.set(node.get('name'), str(size)) 

def vgamem(xml, node):
    size = 2**(int(random.expovariate(1)) + 10)
    xml.cur_xml.set(node.get('name'), str(size)) 

def disk_tray(xml, node):
    if xml.cur_xml.get('bus') in ['floppy', 'cdrom']:
        return True

def disk_removable(xml, node):
    if xml.cur_xml.get('bus') == 'usb':
        return True

def disk_bus(xml, node):
    if xml.xml_stack[-2].find('./driver[@iothread]') is not None:
        xml.cur_xml.set(node.get('name'), 'virtio') 

    if xml.xml_stack[-2].get('device') == 'floppy':
        xml.cur_xml.set(node.get('name'), 'fdc') 

def disk_virtio(xml, node):
    if xml.xml_stack[-2].get('device') != 'floppy':
        return True

def iface_inbound_floor(xml, node):
    if xml.xml_stack[-3].get('type') != 'network':
        pass

def iface_outbound_floor(xml, node):
    pass


def domain_optional(xml, node):
    # TODO: Move to other place
    if node.find("./ref[@name='qemucmdline']") is None:
        return True

    controller = xml.xml.find("./devices/controller[@type='pci']")
    if controller is None:
        node = xml.root.find("./define[@name='pciController']")
        pcinode = xml_gen.parse_node(xml.root, node)
        xml.xml.find("./devices").append(pcinode)
