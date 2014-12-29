import os
import re
import xml.etree.ElementTree as etree
import random
import logging

SCHEMAS_PATH = '/usr/share/libvirt/schemas'


class RngUtils:
    def __init__(self, name='domain'):
        self.root = self.load_rng(os.path.join(SCHEMAS_PATH, name + '.rng'))
        self.start = self.root.findall('./start')[0]
        self.xml = None
        self.temp_value = None
        self.interleave = False
        self.optional = 1
        self.xOrMore = 1
        self.deepth = 0
        self.MAX_DEEPTH = 10
        FORMAT = "%(asctime)-15s %(message)s"
        logging.basicConfig(format=FORMAT, level="INFO")
        self.log = logging.getLogger('RngUtils')
        self.parse_node(self.start, self.xml)
        self._indent(self.xml)

    def _indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def __str__(self):
        return etree.tostring(self.xml)

    def load_rng(self, file_name, is_root=True):
        rng_dir = './'
        path = os.path.join(rng_dir, file_name)
        xml_str = open(path).read()
        xml_str = re.sub(' xmlns="[^"]+"', '', xml_str, count=1)
        root = etree.fromstring(xml_str)
        for node in root.findall('./include'):
            rng_name = os.path.join(SCHEMAS_PATH, node.attrib['href'])
            root.remove(node)
            elements = self.load_rng(rng_name, is_root=False)
            for element in elements:
                root.insert(0, element)
        if is_root:
            return root
        else:
            return root.getchildren()

    def get_ref(self, name):
        return self.root.findall("./*[@name='" + name + "']")[0]

    def get_data(self, node):
        if node is None:
            return "Any string"
        type = node.get('type')
        self.log.debug("Get data: " + type)
        return "0"

    def random_str(self):
        return "random string"

    def parse_node(self, node, xml_node):
        container_tags = ["group", "interleave", "choice", "optional",
                          "zeroOrMore", "oneOrMore", "list", "mixed", "except"]
        selecter_tags = ["choice", "zeroOrMore", "oneOrMore"]
        value_tags = ["value", "data", "text"]
        name_tags = ["name", "anyName", "nsName"]
        if self.deepth > self.MAX_DEEPTH:
            return
        if node.tag == "start":
            self.log.debug("--- START ---")
            combine = node.get('combine')
            if combine is None:
                for child in list(node):
                    self.parse_node(child, xml_node)
            else:
                self.log.error("Start attribute combine is not None")
        elif node.tag == "ref":
            ref_name = node.get('name')
            self.log.debug("ref: " + ref_name)
            new_node = self.get_ref(ref_name)
            self.parse_node(new_node, xml_node)
        elif node.tag == "define":
            name = node.get('name')
            combine = node.get('combine')
            self.log.debug("Read define: " + name)
            if combine is None:
                for child in list(node):
                    self.parse_node(child, xml_node)
            else:
                self.log.error("Attribute combine is not None")
        elif node.tag == "element":
            name = node.get('name')
            children = None
            if name is None:
                self.temp_value = True
                self.parse_node(node[0], xml_node)
                name = self.temp_value
                self.temp_value = None
                children = list(node)[1:]
            if self.xml is None:
                self.log.debug("Create root element: " + name)
                new_xml_node = etree.Element(name)
                self.xml = new_xml_node
            else:
                self.log.debug("Create subelement: " + name)
                new_xml_node = etree.SubElement(xml_node, name)
            self.deepth += 1
            if children is None:
                children = list(node)
            for child in children:
                self.parse_node(child, new_xml_node)
            self.deepth -= 1

        elif node.tag == "attribute":
            name = node.get('name')
            content_index = 0
            if name is None:
                self.log.debug("None attribute name")
                self.temp_value = True
                self.parse_node(node[0], xml_node)
                name = self.temp_value
                self.temp_value = None
                content_index = 1
            self.log.debug("Set attribute: " + name)
            if len(list(node)) == (content_index + 1):
                self.temp_value = True
                self.parse_node(node[content_index], xml_node)
                value = self.temp_value
                self.temp_value = None
                self.log.debug("Get attribute value: " + value)
                xml_node.set(name, value)
            else:
                self.log.debug("Attribute Empty shell: " + name)
                xml_node.set(name, self.get_data(None))
        elif node.tag == "empty":
            pass

        elif node.tag in container_tags:
            if node.tag == "choice":
                self.log.debug("Start random choice")
                choice = random.choice(node.getchildren())
                self.parse_node(choice, xml_node)
            elif node.tag == "optional":
                optional = random.random() < self.optional
                self.log.debug("Enable optional: " + str(optional))
                if optional:
                    self.parse_node(node[0], xml_node)
            elif node.tag == "interleave":
                self.log.debug("Interlever: shuffle children")
                children = list(node)[:]
                if self.interleave:
                    random.shuffle(children)
                for child in children:
                    self.parse_node(child, xml_node)
            elif node.tag == "group":
                self.log.debug("Group elements")
                for child in list(node):
                    self.parse_node(child, xml_node)
            elif node.tag == "zeroOrMore" or node.tag == "oneOrMore":
                self.log.debug("1|0 or more: take samples.")
                children = list(node)[:]
                start = 0
                left = -1
                if node.tag == "oneOrMore":
                    start = 1
                if self.xOrMore == -1:
                    left = random.randint(start, len(children))
                elif self.xOrMore == 0:
                    left = start
                else:
                    left = int(self.xOrMore * len(children))
                self.log.debug("    select {} element(s)".format(left))
                children = random.sample(children, left)
                for child in children:
                    self.parse_node(child, xml_node)
            else:
                self.log.error("Unhandled tag: " + node.tag)
        elif node.tag in value_tags:
            if node.tag == "value":
                self.log.debug("Get value: " + node.text)
                type = node.get('type')
                if self.temp_value:
                    self.temp_value = node.text
                else:
                    if xml_node.text is None:
                        xml_node.text = node.text
                    else:
                        self.log.error('xml_node is not None')
                        xml_node.text += node.text
            elif node.tag == "data":
                self.log.debug("Get data: ")
                data = self.get_data(node)
                if self.temp_value:
                    self.temp_value = "random data"
                else:
                    if xml_node.text is None:
                        xml_node.text = "randome data"
                    else:
                        xml_node.text += "random data"
            elif node.tag == "text":
                self.log.debug("Get text: " + "random text")
                if self.temp_value:
                    self.temp_value = "random text"
                else:
                    if xml_node.text is None:
                        xml_node.text = "random text"
                    else:
                        self.log.error('xml_node is not None')
                        xml_node.text += "random text"
            else:
                self.log.error("Unhandle tag: " + node.tag)
        elif node.tag in name_tags:
            if node.tag == "anyName":
                self.log.debug("User anyName")
                if self.temp_value:
                    self.temp_value = "random text"
                else:
                    if xml_node.text is None:
                        xml_node.text = "random AnyName"
                    else:
                        self.log.error('xml_node is not None')
                        xml_node.text += "random AnyName"
            else:
                self.log.error("Unhandle tag: " + node.tag)
        else:
            self.log.error("Unhandled tag: " + node.tag)
