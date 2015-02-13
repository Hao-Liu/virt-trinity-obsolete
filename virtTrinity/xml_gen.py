import os
import re
import json
import xml.etree.ElementTree as etree
import random
import logging
import utils_random
import utils_xml_gen
from  xml.sax import saxutils


def XMLError(Exception):
    pass


SCHEMAS_PATH = '/usr/share/libvirt/schemas'

def load_rng(file_name, is_root=True):
    xml_str = open(file_name).read()
    xml_str = re.sub(' xmlns="[^"]+"', '', xml_str, count=1)
    nodetree = etree.fromstring(xml_str)
    for node in nodetree.findall('./include'):
        rng_name = os.path.join(SCHEMAS_PATH, node.attrib['href'])
        nodetree.remove(node)
        for element in load_rng(rng_name, is_root=False):
            nodetree.insert(0, element)
    return nodetree if is_root else nodetree.getchildren()


def gen_node(nodename, xml_type='domain'):
    nodetree = load_rng(os.path.join(SCHEMAS_PATH, xml_type + '.rng'))
    for element in load_rng('overides.xml', is_root=False):
        name = element.get('name')
        node = nodetree.find('./define[@name="%s"]' % name)
        if node is not None:
            nodetree.remove(node)
        nodetree.insert(0, element)

    node = nodetree.find("./define[@name='%s']" % nodename)
    return parse_node(nodetree, node)


def parse_node(nodetree, node, parent=None):
    name = node.get('name')
    logging.debug('parsing %s' % node.tag)

    #TODO: Add depth checking
    #TODO: Add node string
    subnodes = list(node)

    if node.tag in ["start", "define"]:
        if len(subnodes) == 1:
            return parse_node(nodetree, subnodes[0], parent)
        elif len(subnodes) > 1:
            if parent is None:
                raise XMLError("Can't start a multi entry <define>")
            result = None
            for subnode in subnodes:
                sgl_res = parse_node(nodetree, subnode, parent)
                if sgl_res is not None:
                    if result is not None:
                        logging.error("Duplicated result in <define>")
                    result = sgl_res
            return result
    elif node.tag == "ref":
        def_nodes = nodetree.findall('./define[@name="%s"]' % name)
        choices = []
        for def_node in def_nodes:
            if not len(node.findall('./notAllowed')):
                choices.append(def_node)
        if choices:
            return parse_node(nodetree, random.choice(choices), parent)
    elif node.tag == "element":
        element = etree.Element(name)
        if parent is not None:
            parent.append(element)

        for subnode in subnodes:
            sgl_res = parse_node(nodetree, subnode, element)
            if type(sgl_res) is str:
                element.text = sgl_res
        return element
    elif node.tag == "attribute":
        if subnodes is not None:
            if subnodes:
                value = parse_node(nodetree, subnodes[0], parent)
            else:
                value = utils_random.text()
        else:
            value = 'anystring'
        parent.set(name, value)
    elif node.tag == "empty":
        pass
    elif node.tag == "optional":
        is_optional = random.random() < 1 # TODO
        if is_optional:
            for subnode in subnodes:
                parse_node(nodetree, subnode, parent)
    elif node.tag == "interleave":
        if False: # TODO
            random.shuffle(subnodes)
        for subnode in subnodes:
            parse_node(nodetree, subnode, parent)
    elif node.tag == "data":
        return get_data(node)
    elif node.tag == "choice":
        choice = random.choice(node.getchildren())
        return parse_node(nodetree, choice, parent)
    elif node.tag == "group":
        for subnode in subnodes:
            parse_node(nodetree, subnode, parent)
    elif node.tag in ["zeroOrMore", "oneOrMore"]:
        if len(subnodes) > 1:
            logging.error("More than one subnodes when xOrMore")

        subnode = subnodes[0]
        min_cnt = 1 if node.tag == "oneOrMore" else 0
        cnt = int(random.expovariate(0.5)) + min_cnt
        for i in xrange(cnt):
            parse_node(nodetree, subnode, parent)
    elif node.tag == "value":
        return node.text
    elif node.tag in ["text", 'anyName']:
        return utils_random.text()
    else:
        logging.error("Unhandled %s" % node.tag)
        exit(1)

def get_data(node, xml=None):
    data_type = node.get('type')
    if data_type in ['short', 'integer', 'int', 'long', 'unsignedShort',
                     'unsignedInt', 'unsignedLong', 'positiveInteger']:
        data_max = 100
        data_min = -100
        if data_type.startswith('unsigned'):
            data_min = 0
        elif data_type == 'positiveInteger':
            data_min = 1

        xml_min = node.findall("./param[@name='minInclusive']")
        xml_max = node.findall("./param[@name='maxInclusive']")
        if xml_min:
            data_min = int(xml_min[0].text)
        if xml_max:
            data_max = int(xml_max[0].text)
        return str(random.randint(data_min, data_max))
    elif data_type == 'double':
        return str(random.expovariate(0.1))
    elif data_type == 'dateTime':
        return "2014-12-25T00:00:01"
    elif data_type == 'NCName':
        return "NCName"
    elif data_type == 'string':
        pattern = node.findall("./param[@name='pattern']")
        pattern = pattern[0].text if pattern else None

        if data_type == 'string' and pattern is None:
            # TODO: Check what happening
            return "NoneString"

        return saxutils.escape(utils_random.regex(pattern))
    elif data_type == 'function':
        fun_name = node.get("function")
        param = node.get("param")
        return getattr(utils_xml_gen, fun_name)(node, param, xml=xml)
    else:
        logging.error("Unhandled data type %s" % data_type)


class RngUtils:
    SCHEMAS_PATH = '/usr/share/libvirt/schemas'
    def __init__(self, name='domain'):
        self.xml = None
        self.xml_stack = []
        self.temp_value = None
        self.interleave = False
        self.optional = 1
        self.MAX_DEEPTH = 100
        self.root = self.load_rng(os.path.join(self.SCHEMAS_PATH, name + '.rng'))
        self.params = {}
        with open('overides.json', 'r') as fp:
            self.overides = json.load(fp)

        for element in self.load_rng('overides.xml', is_root=False):
            name = element.get('name')
            node = self.root.find('./define[@name="%s"]' % name)
            if node is not None:
                self.root.remove(node)
            self.root.insert(0, element)

        self.start = self.root.find('./start')
        self.parse_node(self.start)

        try:
            commandlines = self.xml.findall('./commandline')
            for cmdline in commandlines:
                self.xml.remove(cmdline)
        except IndexError:
            pass
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
        xml_str = open(file_name).read()
        xml_str = re.sub(' xmlns="[^"]+"', '', xml_str, count=1)
        root = etree.fromstring(xml_str)
        for node in root.findall('./include'):
            rng_name = os.path.join(self.SCHEMAS_PATH, node.attrib['href'])
            root.remove(node)
            for element in self.load_rng(rng_name, is_root=False):
                root.insert(0, element)
        return root if is_root else root.getchildren()

    def get_ref(self, name):
        res = self.root.findall("./define[@name='%s']" % name)
        choices = []
        for node in res:
            if not len(node.findall("./notAllowed")):
                choices.append(node)
        if choices:
            return random.choice(choices)

    def parse_node(self, node):
        def get_node_str():
            l = [xml.tag for xml in self.xml_stack]
            name = node.get("name")
            if name is not None:
                l.append(name)
            l.insert(0, "%s " % node.tag)
            return '/'.join(l)

        container_tags = ["group", "interleave", "choice", "optional",
                          "zeroOrMore", "oneOrMore", "list", "mixed", "except"]
        value_tags = ["value", "data", "text"]
        name_tags = ["name", "anyName", "nsName"]

        if len(self.xml_stack) > self.MAX_DEEPTH:
            return

        self.node_str = get_node_str()
        #if re.match('.*idmap.*', self.node_str):
        #    print self.node_str
        #logging.error(node_str)
        if self.node_str in self.overides:
            fun_name = self.overides[self.node_str]
            if not getattr(utils_xml_gen, fun_name)(self, node):
                return

        if node.tag == "start":
            combine = node.get('combine')
            if combine is None:
                for child in list(node):
                    self.parse_node(child)
        elif node.tag == "ref":
            ref_name = node.get('name')
            new_node = self.get_ref(ref_name)
            if new_node is not None:
                for child in list(new_node):
                    self.parse_node(child)
        elif node.tag == "element":
            name = node.get('name')
            children = None
            if self.xml is None:
                self.cur_xml = self.xml = etree.Element(name)
            else:
                self.cur_xml = etree.SubElement(self.cur_xml, name)
            self.xml_stack.append(self.cur_xml)
            if children is None:
                children = list(node)
            for child in children:
                self.parse_node(child)
            if len(self.xml_stack) > 1:
                self.xml_stack.pop()
                self.cur_xml = self.xml_stack[-1]

        elif node.tag == "attribute":
            name = node.get('name')
            content_index = 0
            if name is None:
                if node.find('./anyName'):
                    name = "anyName"
                else:
                    logging.error("Unhandle None attribute: %s" % node)
                content_index = 1
            if len(list(node)) == (content_index + 1):
                self.temp_value = True
                self.parse_node(node[content_index])
                value = self.temp_value
                self.temp_value = None
                self.cur_xml.set(name, value)
            else:
                self.cur_xml.set(name, utils_random.text())
        elif node.tag == "empty":
            pass
        elif node.tag in container_tags:
            if node.tag == "choice":
                choice = random.choice(node.getchildren())
                self.parse_node(choice)
            elif node.tag == "optional":
                optional = random.random() < self.optional
                if optional:
                    for child in list(node):
                        self.parse_node(child)
            elif node.tag == "interleave":
                children = list(node)[:]
                if self.interleave:
                    random.shuffle(children)
                for child in children:
                    self.parse_node(child)
            elif node.tag == "group":
                for child in list(node):
                    self.parse_node(child)
            elif node.tag in ["zeroOrMore", "oneOrMore"]:
                child = list(node)[0]
                if node.tag == "oneOrMore":
                    min_cnt = 1
                else:
                    min_cnt = 0
                cnt = int(random.expovariate(0.5)) + min_cnt
                for i in xrange(cnt):
                    self.parse_node(child)
            else:
                logging.error("Unhandled tag: " + node.tag)
        elif node.tag in value_tags:
            if node.tag == "value":
                if self.temp_value:
                    self.temp_value = node.text
                else:
                    if self.cur_xml.text is None:
                        self.cur_xml.text = node.text
                    else:
                        self.cur_xml.text += node.text
            elif node.tag == "data":
                data = get_data(node, xml=self)
                if data == None:
                    data = "random data"
                if self.temp_value:
                    self.temp_value = data
                else:
                    if self.cur_xml.text is None:
                        self.cur_xml.text = data
                    else:
                        self.cur_xml.text += data
            elif node.tag == "text":
                if self.temp_value:
                    self.temp_value = utils_random.text()
                else:
                    if self.cur_xml.text is None:
                        self.cur_xml.text = "randomtext"
                    else:
                        self.cur_xml.text += "randomtext"
            else:
                logging.error("Unhandle tag: " + node.tag)
        elif node.tag in name_tags:
            if node.tag == "anyName":
                if self.temp_value:
                    self.temp_value = utils_random.text()
                else:
                    if self.cur_xml.text is None:
                        self.cur_xml.text = "random AnyName"
                    else:
                        logging.error('self.cur_xml is not None')
                        self.cur_xml.text += "random AnyName"
            else:
                logging.error("Unhandle tag: " + node.tag)
        else:
            logging.error("Unhandled tag: " + node.tag)
