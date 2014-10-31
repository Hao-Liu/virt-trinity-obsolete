import random
import string


def random_string(escape=True, min_len=1, max_len=10):
    """
    Generate a randomized string.
    """

    excludes = "\n\t\r\x0b\x0c"
    escapes = """~()[]{}<>|&$#?'"`*; \n\t\r\\"""

    chars = []
    for char in string.printable:
        if char not in excludes:
            if char in escapes:
                chars.append('\\' + char)
            else:
                chars.append(char)

    length = random.randint(min_len, max_len)

    return ''.join(random.choice(chars) for _ in xrange(length))


def random_int():
    """
    Return an randomized integer.
    """

    return random.randint(-2, 100)
