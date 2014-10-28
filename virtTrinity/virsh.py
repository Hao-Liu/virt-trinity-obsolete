import os
import json
import random
import command
import subprocess
import itertools


class Virsh(object):
    commands = {}

    def __init__(self):
        self.commands = self.load_virsh_cmds()

    def get_virsh_cmds_from_help(self):
        virsh_cmds = {}
        for line in subprocess.check_output(['virsh', 'help']).splitlines():
            if line.startswith('    '):
                cmd_name = line.split()[0]
                virsh_cmds[cmd_name] = command.Command(cmd_name)

        return virsh_cmds

    def load_virsh_cmds(self):
        if os.path.isfile('virsh_cmds.json'):
            virsh_cmds = {}
            with open('virsh_cmds.json', 'r') as json_file:
                serialized_cmds = json.load(json_file)
            for cmd_name in serialized_cmds:
                serialized_cmd = serialized_cmds[cmd_name]
                json_txt = json.dumps(serialized_cmd)
                virsh_cmds[cmd_name] = command.Command.from_json(json_txt)
        else:
            virsh_cmds = self.get_virsh_cmds_from_help()
            serializable_cmds = {}
            for cmd_name in virsh_cmds:
                serializable_cmd = json.loads(virsh_cmds[cmd_name].to_json())
                serializable_cmds[cmd_name] = serializable_cmd
            with open('virsh_cmds.json', 'w') as json_file:
                json.dump(serializable_cmds, json_file, sort_keys=True,
                          indent=4)
        return virsh_cmds

    def gen_random_cmdline_from_cmd(self, cmd):
        cmdline = 'virsh ' + cmd.short_name
        for option in cmd.options:
            if option.required or random.random() < 0.5:
                cmdline += ' --' + option.name
                if option.type == 'string':
                    cmdline += ' somestring'
                elif option.type == 'number':
                    cmdline += ' 123123'
        return cmdline

    def get_random_cmd(self, commands=[]):
        if commands:
            cmd_name = random.choice(commands)
        else:
            cmd_name = random.choice(self.commands.keys())

        cmd = self.commands[cmd_name]
        return cmd

    def get_random_cmdline(self, commands=[]):
        command = self.get_random_cmd(commands=commands)
        return self.gen_random_cmdline_from_cmd(command)

    def iter_cmdline(self, cmd_name):
        command = self.commands[cmd_name]
        if 'opt_iter' not in dir(command):
            types_list = []
            for option in command.options:
                type_list = option.type_list()
                if type_list:
                    types_list.append(type_list)
            command.opt_iter = itertools.product(*types_list)

        opt_list = [opt for opt in command.opt_iter.next() if opt]
        return 'virsh %s ' % cmd_name + ' '.join(opt_list)

    def cmdline_generator(self, cmd_name):
        command = self.commands[cmd_name]
        types_list = []
        for option in command.options:
            type_list = option.type_list()
            if type_list:
                types_list.append(type_list)
        opt_iter = itertools.product(*types_list)
        for opt_list in opt_iter:
            opt_list = [opt for opt in opt_list if opt]
            yield 'virsh %s ' % cmd_name + ' '.join(opt_list)
