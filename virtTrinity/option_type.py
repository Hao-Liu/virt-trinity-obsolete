class OptionType(object):
    all_types = {
        'bool': [
            'set',
            'not_set',
        ],
        'string': [
            'some_string',
            'not_set',
        ],
        'domain': [
            'running_domain',
            'not_set',
        ],
    }

    def parse_set(self, opt_name):
        return '--%s' % opt_name

    def parse_not_set(self, opt_name):
        return ''

    def parse_running_domain(self, opt_name):
        return '--%s virt-fsm-running' % opt_name

    def parse_some_string(self, opt_name):
        return '--%s some_string' % opt_name

    def __init__(self, opt_type):
        self.types = self.all_types[opt_type]

    def parse_types(self, opt_name):
        parsed_types = []
        for opt_type in self.types:
            parse_fun = getattr(self, 'parse_' + opt_type)
            parsed_types.append(parse_fun(opt_name))
        return parsed_types
