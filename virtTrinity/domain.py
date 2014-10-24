import os

def renew(vm_name):
    os.system('virsh undefine virt-fsm-running')
    xml = """
<domain type='qemu'>
  <name>%s</name>
  <memory unit='KiB'>100000</memory>
  <currentMemory unit='KiB'>100000</currentMemory>
  <os>
    <type arch='x86_64' machine='pc-i440fx-2.1'>hvm</type>
  </os>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
  </devices>
</domain>
    """ % vm_name
    xml_file = '/tmp/vm_xml'
    with open(xml_file, 'w') as tmp_xml:
        tmp_xml.write(xml)
    os.system('virsh create %s' % xml_file)

def prepare_running():
    print 'hello'
    renew('virt-fsm-running')
