import json
import requests
import datetime


class Client(object):
    def start_run(self, run_id):
        cur_time = datetime.datetime.now().isoformat()
        requests.post(
            "http://127.0.0.1:8000/run",
            data=json.dumps(
                {
                    "start": cur_time,
                    "uuid": str(run_id),
                    "action": "start",
                }
            )
        )

    def end_run(self, run_id):
        cur_time = datetime.datetime.now().isoformat()
        requests.post(
            "http://127.0.0.1:8000/run",
            data=json.dumps(
                {
                    "end": cur_time,
                    "uuid": str(run_id),
                    "action": "end",
                }
            )
        )

    def send_result(self, run_id, cmd_id, result):
        requests.post(
            "http://127.0.0.1:8000/result",
            data=json.dumps(
                {
                    "run": str(run_id),
                    "id": cmd_id,
                    "cmdname": result.cmdname,
                    "cmdline": result.cmdline,
                    "status": result.exit_status,
                    "duration": result.call_time,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "sub_stdout": result.sub_stdout,
                    "sub_stderr": result.sub_stderr,
                    "key": result.key,
                }
            )
        )
