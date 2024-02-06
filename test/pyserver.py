#!/usr/bin/env python3
# coding: utf-8
#
# 测试pyagent功能 web server


import sys
import os
from flask import Flask, request
import json

lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from tlog import Tlog
from restful import api_info

log = Tlog()


def auth(headers)->bool:
    return headers.get('username') == api_info.worker_username and \
           headers.get('password') == api_info.worker_password


app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello():
    return f"hello, this is the Test Web Server"


@app.route('/job/report', methods=['POST'])
def service_report():
    if auth(request.headers):
        try:
            job_info = request.json.get('job')
            log.info(f"job info received:\n{job_info}")
            return json.dumps({
                "code": 200,
                "success": 'true',
                "message": "update job success!",
                "result": {
                    "job": job_info['id']
                }
            })
        except Exception as e:
            return json.dumps({
                "code": 400,
                "success": 'false',
                "message": f"update job failed: {str(e)}",
                "result": {
                    "job": job_info['id']
                }
            })
    else:
        return json.dumps({
            "code": 400,
            "success": 'false',
            "message": "invalid username or password!"
        })


if __name__ == '__main__':
    log.info(f"server app running(pid={os.getpid()})")
    app.run(
        host='127.0.0.1',
        port='3000',
        debug=False
    )
