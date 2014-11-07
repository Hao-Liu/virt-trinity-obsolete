import copy


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')


@Singleton
class ResultManager(object):

    def __init__(self):
        self.result_list = []
        self.cmd_list = {}
        self.json_list = []
        self.result_stats = {}

    def append(self, cmd_line, result):
        def canonicalize(cmd_line, result):
            new_result = copy.copy(result)
            for attr in ['stdout', 'stderr']:
                text = '\n'.join(getattr(new_result, attr))
                text = text.decode('utf-8')
                for opt in cmd_line.options:
                    line = opt['line']
                    replacement = '${%s}' % opt['option'].name
                    if line and line in text:
                        text = text.replace(line, replacement)
                setattr(new_result, attr, text)
            return new_result

        self.result_list.append(result)
        self.json_list.append(result.prepare_for_html())

        if result.exit_status is None:
            exit_status = "timeout"
        elif result.exit_status == 0:
            exit_status = "success"
        elif result.exit_status > 0:
            exit_status = "failure"

        cmd_name = cmd_line.name
        if cmd_name not in self.result_stats:
            self.result_stats[cmd_name] = {
                "timeout": 0,
                "success": 0,
                "failure": 0,
                "results": {},
            }

        self.result_stats[cmd_name][exit_status] += 1
        new_result = canonicalize(cmd_line, result)
        result_key = '\n'.join((
            exit_status,
            new_result.stdout,
            new_result.stderr
        ))
        if result_key not in self.result_stats[cmd_name]["results"]:
            self.result_stats[cmd_name]["results"][result_key] = {
                'exit_status': exit_status,
                'stdout': new_result.stdout,
                'stderr': new_result.stderr,
                'cmdlines': [],
            }

        self.result_stats[cmd_name]["results"][result_key]['cmdlines'].append(
            str(cmd_line))

    def log(self, idx, count):
        total_len = len(self.json_list)
        if total_len > idx + count:
            return self.json_list[idx:idx+count]
        elif total_len > idx:
            return self.json_list[idx:]
        else:
            return []

    def cmd(self, cmd_name):
        if cmd_name in self.result_stats:
            return self.result_stats[cmd_name]["results"]
        else:
            return {}

    def stats(self):
        data = []
        stat_color_map = (
            ('success', '#99ff00'),
            ('failure', '#cc0000'),
            ('timeout', '#ffcc00'),
        )
        for exit_status, color in stat_color_map:
            count_points = sorted([{"label": cmd, "y": stat[exit_status]}
                                   for cmd, stat in self.result_stats.items()])
            count_points.reverse()
            data.append({
                "type": "stackedBar",
                "showInLegend": True,
                "name": exit_status.title(),
                "axisYType": "secondary",
                "color": color,
                "dataPoints": count_points,
            })
        return data
