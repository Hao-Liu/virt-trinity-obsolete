import os
import errno
import time
import fcntl
import select
import signal
import subprocess


class CmdResult(object):
    """A class representing the result of a system call.
    """

    def __init__(self, cmdline):
        self.cmdline = cmdline
        self.stdout = []
        self.stderr = []
        self.exit_status = None
        self.call_time = 0.0

    def pprint(self):
        """
        Print the command result in a pretty and colorful way.
        """
        tty_h, tty_w = subprocess.check_output(['stty', 'size']).split()

        print '\033[94m%-177s\033[93m%-3s\033[0m%.3f' % (
            self.cmdline, self.exit_status, self.call_time)
        for line in self.stdout:
            print line
        for line in self.stderr:
            print '\033[91m%s\033[0m' % line


def run(cmdline, timeout=10):
    """Run the command line and return the result with a CmdResult object.

    :param cmdline: The command line to run.
    :type cmdline: str.
    :param timeout: After which the calling processing is killed.
    :type timeout: float.
    :returns: CmdResult -- the command result.
    :raises:
    """
    start = time.time()
    process = subprocess.Popen(
        cmdline,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid,
    )

    fcntl.fcntl(
        process.stdout,
        fcntl.F_SETFL,
        fcntl.fcntl(process.stdout, fcntl.F_GETFL) | os.O_NONBLOCK,
    )
    fcntl.fcntl(
        process.stderr,
        fcntl.F_SETFL,
        fcntl.fcntl(process.stderr, fcntl.F_GETFL) | os.O_NONBLOCK,
    )

    result = CmdResult(cmdline)

    try:
        while True:
            select.select([process.stdout, process.stderr], [], [], 0.1)
            try:
                out_lines = process.stdout.read()
                if out_lines:
                    for line in out_lines.splitlines():
                        result.stdout.append(line)
                err_lines = process.stderr.read()
                if err_lines:
                    for line in err_lines.splitlines():
                        result.stderr.append(line)
            except IOError, detail:
                if detail.errno != errno.EAGAIN:
                    raise detail

            exit_status = process.poll()
            result.call_time = (time.time() - start)

            if exit_status is not None:
                result.exit_status = exit_status
                return result

            if result.call_time > timeout:
                return result
    finally:
        if result.exit_status is None:
            pgid = os.getpgid(process.pid)
            os.killpg(pgid, signal.SIGKILL)

        # Reset tty to clean console caused by killing console or editor
        subprocess.call(["stty", "sane"])
        # Restore disabled scrolling caused by killing editor
        subprocess.call(["tput", "rmcup"])
