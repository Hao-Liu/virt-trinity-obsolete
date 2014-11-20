import sqlite3


class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect('virt-trinity.db')

    def create(self):
        with self.conn:
            self.conn.execute(
                'create table if not exists runs (start, end, uuid, status)')
            self.conn.execute(
                'create table if not exists results (run, id, cmdname, '
                'cmdline, status, duration, stdout, stderr, sub_stdout, '
                'sub_stderr, key)')

    def update_run(self, content):
        if content['action'] == 'start':
            with self.conn:
                self.conn.execute(
                    "insert into runs values(?,null,?,'running')",
                    (
                        content['start'],
                        content['uuid'],
                    )
                )
        elif content['action'] == 'end':
            with self.conn:
                self.conn.execute(
                    "update runs set status='finished',end=? where uuid=?",
                    (
                        content['end'],
                        content['uuid'],
                    )
                )

    def insert_result(self, content):
        with self.conn:
            self.conn.execute(
                'insert into results values(?,?,?,?,?,?,?,?,?,?,?)',
                (
                    content['run'],
                    content['id'],
                    content['cmdname'],
                    content['cmdline'],
                    content['status'],
                    content['duration'],
                    content['stdout'],
                    content['stderr'],
                    content['sub_stdout'],
                    content['sub_stderr'],
                    content['key'],
                )
            )

    def get_results(self, start_idx, count):
        cur = self.conn.cursor()
        cur.execute(
            "select * from results where id >= ? and id <= ?",
            (start_idx, start_idx + count)
        )
        results = cur.fetchall()
        ret = []
        for (run, idx, cmdname, cmdline, status, duration,
             stdout, stderr, sub_stdout, sub_stderr, key) in results:
            ret.append({
                "cmdline": cmdline,
                "exit_status": status,
                "stdout": stdout,
                "stderr": stderr,
                "sub_stdout": sub_stdout,
                "sub_stderr": sub_stderr,
                "key": key,
            })
        return ret

    def get_command(self, name):
        cur = self.conn.cursor()
        cur.execute(
            "select * from results where cmdname=?",
            (name,)
        )
        results = cur.fetchall()
        ret = []
        for (run, idx, cmdname, cmdline, status, duration,
             stdout, stderr, sub_stdout, sub_stderr, key) in results:
            ret.append({
                "cmdline": cmdline,
                "exit_status": status,
                "stdout": stdout,
                "stderr": stderr,
                "sub_stdout": sub_stdout,
                "sub_stderr": sub_stderr,
                "key": key,
            })
        return ret

    def get_stat(self):
        cur = self.conn.cursor()
        stat = {}
        for status in ("success", "failure", "timeout"):
            cur.execute(
                "select distinct cmdname, count(cmdname) from results "
                "where status is ? group by cmdname",
                (status,)
            )
            for name, cnt in cur.fetchall():
                if name not in stat:
                    stat[name] = {"success": 0, "failure": 0, "timeout": 0}
                stat[name][status] = cnt
        return sorted(stat.items())
