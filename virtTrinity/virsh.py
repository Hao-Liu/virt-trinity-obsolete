import os
import json
import command
import subprocess
import itertools

import utils


class Virsh(object):

    def __init__(self):
        self.commands = {}
        self.load_virsh_cmds()

    def load_from_help(self):
        virsh_cmds = {}
        for line in subprocess.check_output(['virsh', 'help']).splitlines():
            if line.startswith('    '):
                cmd_name = line.split()[0]
                virsh_cmds[cmd_name] = command.Command.from_help(cmd_name)
        return virsh_cmds

    def to_json(self):
        virsh_cmds = {}
        for cmd_name in self.commands:
            cmd = json.loads(self.commands[cmd_name].to_json())
            virsh_cmds[cmd_name] = cmd

        json_txt = json.dumps(virsh_cmds, sort_keys=True, indent=4)
        return json_txt

    def from_json(self, json_txt):
        virsh_cmds = json.loads(json_txt)
        for cmd_name in virsh_cmds:
            json_txt = json.dumps(virsh_cmds[cmd_name])
            virsh_cmds[cmd_name] = command.Command.from_json(json_txt)
        return virsh_cmds

    def load_virsh_cmds(self):
        if os.path.isfile('virsh_cmds.json'):
            with open('virsh_cmds.json', 'r') as json_file:
                json_txt = json_file.read()
            self.commands = self.from_json(json_txt)
        else:
            self.commands = self.load_from_help()

            json_txt = self.to_json()
            with open('virsh_cmds.json', 'w') as json_file:
                json_file.write(json_txt)

    def random_cmd(self, commands=[]):
        if commands:
            cmds = [self.commands[name] for name in commands]
            cmd = utils.weighted_choice(cmds)
        else:
            cmd = utils.weighted_choice(self.commands)

        return command.RunnableCommand.random(cmd)

    def iter_cmdline(self, cmd_name):
        cmd = self.commands[cmd_name]
        if 'opt_iter' not in dir(cmd):
            types_list = []
            for option in cmd.options:
                type_list = option.type_list()
                if type_list:
                    types_list.append(type_list)
            cmd.opt_iter = itertools.product(*types_list)

        opt_list = [opt for opt in cmd.opt_iter.next() if opt]
        return 'virsh %s ' % cmd_name + ' '.join(opt_list)

    def cmdline_generator(self, cmd_name):
        cmd = self.commands[cmd_name]
        types_list = []
        for option in cmd.options:
            type_list = option.type_list()
            if type_list:
                types_list.append(type_list)
        opt_iter = itertools.product(*types_list)
        for opt_list in opt_iter:
            opt_list = [opt for opt in opt_list if opt]
            yield 'virsh %s ' % cmd_name + ' '.join(opt_list)
