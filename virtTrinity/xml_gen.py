import os
import re
import xml.etree.ElementTree as etree
import random
import logging
import utils_random
import utils_xml_gen
from xml.sax import saxutils


class XMLError(Exception):
    pass


SCHEMAS_PATH = '/usr/share/libvirt/schemas'
MAX_DEEPTH = 100


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


def gen_node(nodename=None, xml_type='domain', sanity='startable'):
    nodetree = load_rng(os.path.join(SCHEMAS_PATH, xml_type + '.rng'))
    for element in load_rng('overides.xml', is_root=False):
        name = element.get('name')
        node = nodetree.find('./define[@name="%s"]' % name)
        if node is not None:
            nodetree.remove(node)
        nodetree.insert(0, element)

    if nodename is None:
        node = nodetree.find("./start")
    else:
        node = nodetree.find("./define[@name='%s']" % nodename)

    params = {
        'xml_stack': [],
        'node_stack': [],
        'nodetree': nodetree,
        'sanity': sanity,
    }
    return parse_node(node, params=params)


def parse_node(node, params=None):
    xml_stack = params['xml_stack']
    node_stack = params['node_stack']
    nodetree = params['nodetree']

    if len(xml_stack) > MAX_DEEPTH:
        return

    name = node.get('name')
    logging.debug('parsing %s' % node.tag)

    xml_tags = [xml.tag for xml in xml_stack]
    if name is None:
        path_seg = node.tag
    else:
        path_seg = '%s[@name="%s"]' % (node.tag, name)
        xml_tags.append(name)

    if node.tag in ["start", "define"]:
        params['node_stack'] = [path_seg]
    else:
        params['node_stack'].append(path_seg)

    xml_path = '/' + '/'.join(xml_tags)
    node_path = '/' + '/'.join([tag for tag in node_stack])

    cont, result = utils_xml_gen.process_overide(
        node.tag, xml_path, node_path, node, params)
    if cont is not True:
        return result

    subnodes = list(node)

    if node.tag in ["start", "define"]:
        if len(subnodes) == 1:
            return parse_node(subnodes[0], params)
        elif len(subnodes) > 1:
            result = None
            for subnode in subnodes:
                sgl_res = parse_node(subnode, params)
                if sgl_res is not None:
                    if result is not None:
                        # TODO: Fix this
                        logging.debug("Duplicated result in <define>")
                    result = sgl_res
            return result
    elif node.tag == "ref":
        def_nodes = nodetree.findall('./define[@name="%s"]' % name)
        choices = []
        for def_node in def_nodes:
            if not len(def_node.findall('./notAllowed')):
                choices.append(def_node)
        if choices:
            return parse_node(random.choice(choices), params)
    elif node.tag == "element":
        if node.find('./anyName') is not None:
            name = utils_random.text()
        if name is None:
            raise XMLError('Cannot find element name: %s' %
                           etree.tostring(node))
        element = etree.Element(name)
        if len(xml_stack):
            xml_stack[-1].append(element)
        xml_stack.append(element)
        for subnode in subnodes:
            sgl_res = parse_node(subnode, params)
            if type(sgl_res) is str:
                element.text = sgl_res
        if len(xml_stack) > 1:
            xml_stack.pop()
        return element
    elif node.tag == "attribute":
        if subnodes is not None:
            if subnodes:
                value = parse_node(subnodes[0], params)
            else:
                value = saxutils.escape(
                    utils_random.text(),
                    entities={"'": "&apos;", "\"": "&quot;"}
                )
        else:
            value = 'anystring'
        if value is not None:
            xml_stack[-1].set(name, value)
    elif node.tag == "empty":
        pass
    elif node.tag == "optional":
        # TODO
        is_optional = random.random() < 1
        if is_optional:
            for subnode in subnodes:
                parse_node(subnode, params)
    elif node.tag == "interleave":
        if False:
            # TODO
            random.shuffle(subnodes)
        for subnode in subnodes:
            parse_node(subnode, params)
    elif node.tag == "data":
        return get_data(node)
    elif node.tag == "choice":
        choice = random.choice(node.getchildren())
        return parse_node(choice, params)
    elif node.tag == "group":
        for subnode in subnodes:
            parse_node(subnode, params)
    elif node.tag in ["zeroOrMore", "oneOrMore"]:
        if len(subnodes) > 1:
            logging.error("More than one subnodes when xOrMore")

        subnode = subnodes[0]
        min_cnt = 1 if node.tag == "oneOrMore" else 0
        cnt = int(random.expovariate(0.5)) + min_cnt
        for i in xrange(cnt):
            parse_node(subnode, params)
    elif node.tag == "value":
        return node.text
    elif node.tag in ["text", 'anyName']:
        return saxutils.escape(
            utils_random.text(),
            entities={"'": "&apos;", '"': "&quot;"}
        )
    elif node.tag == 'anyURI':
        # TODO: generate random URI.
        return "qemu:///system"
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

        return utils_random.regex(pattern)
    else:
        logging.error("Unhandled data type %s" % data_type)


class RngUtils:
    SCHEMAS_PATH = '/usr/share/libvirt/schemas'

    def __init__(self, name='domain', sanity='startable'):
        self.interleave = False
        self.optional = 1
        self.MAX_DEEPTH = 100
        self.params = {}
        self.xml = gen_node(xml_type=name, sanity=sanity)

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
