import re
import random
import string
import utils
import logging
import xml_gen
from xml_gen import RngUtils
from xml.etree import ElementTree

def cpuset():
    return "^1,0-3"

def integer(min_inc, max_inc):
    return random.randint(min_inc, max_inc)

def text(escape=False, min_len=5, max_len=10):
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
    return "randomtext"

ALL_CHARS = set(string.letters)
def regex(regex):
    """
    Generate a random string matches given regular expression.
    """
    def _end_chose(chosen, cmin, cmax):
        current_group = result_stack[-1]
        current_group.append((chosen, cmin, cmax, neg_chose))

    def _start_group():
        current_group = [[]]
        result_stack.append(current_group[0])
        result_stack[-2].append(current_group)

    def _end_sub_group():
        current_sub_group = []
        result_stack[-2][-1].append(current_sub_group)
        result_stack.pop()
        result_stack.append(current_sub_group)

    def _end_group(cmin, cmax):
        parent_group = result_stack[-2]
        result_stack.pop()
        parent_group.append((tuple(parent_group.pop()), cmin, cmax))

    def _randomize(stack):
        if len(stack) == 3:
            sub_stacks, cmin, cmax = stack
            assert type(sub_stacks) == tuple
            sub_stacks = random.choice(sub_stacks)
            assert type(sub_stacks) == list
        elif len(stack) == 4:
            chose_str, cmin, cmax, neg = stack
            sub_stacks = None
            assert type(chose_str) == str
            if neg:
                chose_str = ''.join(ALL_CHARS - set(chose_str))

        if cmax is None:
            count = int(random.expovariate(0.1)) + cmin
        else:
            count = random.randint(cmin, cmax)

        rnd_str = ""
        if sub_stacks is not None:
            for i in xrange(count):
                for sub_stack in sub_stacks:
                    rnd_str += _randomize(sub_stack)
        else:
            for i in xrange(count):
                rnd_str += random.choice(chose_str)
        return rnd_str

    spanning = False
    escaping = False

    chosen = []
    choosing = False
    neg_chose = False

    counting = None
    count_min = 0
    count_max = None

    root_result = []
    result_stack = [[root_result], root_result]

    _start_group()
    for idx, c in enumerate(regex):
        if choosing:
            if c == '^' and neg_chose:
                continue

            if spanning:
                span_from = chosen[-1]
                span_to = c
                cur = ord(span_from)
                while cur < ord(span_to):
                    cur += 1
                    chosen += chr(cur)
                spanning = False
                continue

            if escaping:
                if c == 'n':
                    chosen += '\n'
                elif c == 't':
                    chosen += '\t'
                elif c == 'r':
                    chosen += '\r'
                else:
                    chosen += c
                escaping = False
                continue

            if c == ']':
                choosing = False
                if idx < len(regex) - 1 and regex[idx + 1] in '{?+*':
                    counting = 'chose'
                else:
                    _end_chose(chosen, 1, 1)
                continue

            if c == '-':
                spanning = True
                continue

            if c == '\\':
                escaping = True
                continue

            else:
                chosen += c
                continue

        if counting:
            if c == ',':
                count_max = 0
                continue

            if c == '}':
                if count_max is None:
                    count_max = count_min
                if counting == 'chose':
                    _end_chose(chosen, count_min, count_max)
                elif counting == 'group':
                    _end_group(count_min, count_max)
                else:
                    logging.error("Unknown counting type %s" % counting)
                counting = None
                continue
            if c in string.digits:
                if count_max is None:
                    count_min = 10 * count_min + int(c)
                else:
                    count_max = 10 * count_max + int(c)
                continue
            if c == '{':
                count_min = 0
                count_max = None
                continue
            if c in '?+*':
                count_min = 0
                count_max = None
                if c == '+':
                    count_min = 1
                if c == '?':
                    count_max = 1
                if counting == 'chose':
                    _end_chose(chosen, count_min, count_max)
                elif counting == 'group':
                    _end_group(count_min, count_max)
                else:
                    logging.error("Unknown counting type %s" % counting)
                counting = None
                continue
            logging.error("Unhandled counting character: %s" % c)

        if escaping:
            _end_chose(c, 1, 1)
            escaping = False
            continue

        if c == '(':
            _start_group()
            continue

        if c == ')':
            if idx < len(regex) - 1 and regex[idx + 1] in '{?+*':
                counting = 'group'
            else:
                _end_group(1, 1)
            continue

        if c == '[':
            choosing = True
            neg_chose = (regex[idx + 1] == '^')
            chosen = ''
            continue

        if c == '\\':
            escaping = True
            continue

        if c == '|':
            _end_sub_group()
            continue

        chosen = c
        if idx < len(regex) - 1 and regex[idx + 1] in '{?+*':
            counting = 'chose'
        else:
            _end_chose(chosen, 1, 1)
        continue
    _end_group(1, 1)
    return _randomize(result_stack[0][0][0])

def xml(xml_type, name=None):
    xml_str = str(RngUtils(xml_type))
    if name is not None:
        xml_str = re.sub(r'(?<=\<name\>)\S*(?=\<\/name\>)', name, xml_str)
    return xml_str

def device_xml(dev_type=None):
    dev_types = [
        'disk',
        'controller',
        'lease',
        'lease',
        'filesystem',
        'interface',
        'input',
        'sound',
        'hostdev',
        'graphic',
        'video',
        'console',
        'parallel',
        'serial',
        'channel',
        'smartcard',
        'hub',
        'redirdev',
        'redirfilter',
        'rng',
        'tpm',
        'shmem',
        'emulator',
        'watchdog',
        'memballoon',
        'nvram',
        'panic',
    ]
    if dev_type is None:
        dev_type = random.choice(dev_types)
    return ElementTree.tostring(xml_gen.gen_node('devices'))
