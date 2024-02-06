#!/usr/bin/env python3
# coding: utf-8
# 
# worker app
# 部署: 运行后，(/schedule/start)启动 scheduler


import sys
import os
from flask import Flask, request
import json
import subprocess
import multiprocessing
import signal
import time
from gevent.pywsgi import WSGIServer
from colorama import init as TermInit


lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from tlog import Tlog
from restful import api_info
from agent import Agent
from agent import JOB_STATUS_NEW, JOB_STATUS_WAIT, JOB_STATUS_RUN, JOB_STATUS_STOP, JOB_STATUS_DONE, JOB_STATUS_TMOUT

# 终端初始化(颜色打印偶尔失效)
TermInit(autoreset=True)

job_path_new = api_info.worker_job_path['new']
job_path_waiting = api_info.worker_job_path['wait']
job_path_running = api_info.worker_job_path['run']
job_path_done = api_info.worker_job_path['done']
job_path_stop = api_info.worker_job_path['stop']


log = Tlog()


def init()->bool:
    """ 初始化工作空间
    """
    for layer in (job_path_new, job_path_waiting, job_path_running, job_path_done, job_path_stop):
        if not os.path.exists(layer):
            try:
                os.makedirs(layer)
            except Exception as e:
                log.error(f"failed to create worker layer: {layer}\n{e}")
                return False
    return True


def auth(headers, module='job')->bool:
    success = headers.get('username') == api_info.server_username and \
              headers.get('password') == api_info.server_password

    if module == f'schedule':
        success = success and headers.get('Host') == f'127.0.0.1:{api_info.worker_port}' and \
                              headers.get('Referer') == f'127.0.0.1:{api_info.worker_port}'
    return success


def check_job(job_id: str)->str:
    """ 获取job当前真实json
    """
    test_file1 = os.path.join(job_path_new, f'{job_id}.json')
    test_file2 = os.path.join(job_path_waiting, f'{job_id}.json')
    test_file3 = os.path.join(job_path_running, f'{job_id}.json')
    test_file4 = os.path.join(job_path_done, f'{job_id}.json')
    if os.path.isfile(test_file1):
        return test_file1
    elif os.path.isfile(test_file2):
        return test_file2
    elif os.path.isfile(test_file3):
        return test_file3
    elif os.path.isfile(test_file4):
        return test_file4
    else:
        return None


def new_job(job_info: dict)->tuple:
    """ 创建运行任务
    """
    try:
        job_id = job_info['id']

        if check_job(job_id) is not None:
            return (False, f'job exists already!')

        job_info['status'] = JOB_STATUS_NEW
        job_info['ppid'] = ''
        job_info['pid'] = ''

        if not os.path.isdir(job_path_new):
            os.makedirs(job_path_new)

        job_json_file = os.path.join(job_path_new, f'{job_id}.json')
        with open(job_json_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(job_info))

        return (True, None)

    except Exception as e:
        return (False, str(e))


def new_stop_job(job_info: dict)->tuple:
    """ 创建停止任务
    """
    try:
        job_id = job_info['id']

        if check_job(job_id) is None:
            return (False, f'job not found!')

        if not os.path.isdir(job_path_stop):
            os.makedirs(job_path_stop)

        job_json_file = os.path.join(job_path_stop, f'{job_id}.json')
        with open(job_json_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(job_info))

        return (True, None)

    except Exception as e:
        return (False, str(e))


def query_job(job_id: str)->tuple:
    """ 查询job状态
    """
    job_file = check_job(job_id)
    if not job_file:
        return (False, "job not found!", {"id": job_id})

    with open(job_file, 'r', encoding='utf-8') as f:
        job_info = json.loads(f.read(), encoding='utf-8')

    if job_info['status'] == JOB_STATUS_RUN:
        return (True, f"agent(pid={job_info['ppid']})/job(pid={job_info['pid']}) running", job_info)
    elif job_info['status'] == JOB_STATUS_TMOUT:
        return (True, f"agent(pid={job_info['ppid']})/job(pid={job_info['pid']}) timeout exited", job_info)
    elif job_info['status'] == JOB_STATUS_STOP:
        return (True, f"agent(pid={job_info['ppid']})/job(pid={job_info['pid']}) stopped exited", job_info)
    elif job_info['status'] == JOB_STATUS_WAIT:
        return (True, f"agent(pid={job_info['ppid']})/job(pid={job_info['pid']}) waiting", job_info)
    elif job_info['status'] == JOB_STATUS_DONE:
        return (True, f"agent(pid={job_info['ppid']})/job(pid={job_info['pid']}) finished exited", job_info)
    else:
        return (True, f"agent(pid={job_info['ppid']})/job(pid={job_info['pid']}) created success", job_info)


def update_job(job_json_file: str, new_status: str)->tuple:
    if not os.path.isfile(job_json_file):
        return (False, job_json_file)
    if new_status not in (JOB_STATUS_WAIT, JOB_STATUS_RUN, JOB_STATUS_TMOUT, JOB_STATUS_DONE, JOB_STATUS_STOP):
        return (False, job_json_file)

    if new_status in (JOB_STATUS_DONE, JOB_STATUS_STOP):
        new_layer = f'done'
    else:
        new_layer = new_status
    
    try:
        with open(job_json_file, 'r', encoding='utf-8') as f:
            job_info = json.loads(f.read())

        dir_json_new = os.path.realpath(os.path.join(os.path.dirname(job_json_file), '..', new_layer))
        if not os.path.isdir(dir_json_new):
            os.makedirs(dir_json_new)

        new_json_file = os.path.join(dir_json_new, os.path.basename(job_json_file))
        job_info['status'] = new_status
        with open(new_json_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(job_info))
        os.remove(job_json_file)

        return (True, new_json_file)
    except Exception as e:
        log.error(f"update job status failed: {job_json_file}\n{e}")
        return (False, job_json_file)


def check_layer_idle(layer: str)->tuple:
    """ 检查指定layer是否空闲
    """
    if layer == f'wait':
        layer_path = job_path_waiting
    elif layer == f'run':
        layer_path = job_path_running
    else:
        return (False, 0)

    if not os.path.isdir(layer_path):
        os.makedirs(layer_path)

    layer_list = os.listdir(layer_path)
    if not layer_list:
        return (True, api_info.worker_parallel_jobs)
    elif len(layer_list) < api_info.worker_parallel_jobs:
        return (True, api_info.worker_parallel_jobs-len(layer_list))
    else:
        return (False, 0)


def commit_jobs(new_status: str)->None:
    """ 提交job
    """
    if new_status == JOB_STATUS_WAIT:
        check_layer = f'wait'
        current_job_path = job_path_new
    elif new_status == JOB_STATUS_RUN:
        check_layer = f'run'
        current_job_path = job_path_waiting
    else:
        return

    idle, adds = check_layer_idle(check_layer)
    if not idle:
        return
    if not os.path.isdir(current_job_path):
        os.makedirs(current_job_path)
    tobe_list = os.listdir(current_job_path)
    if not tobe_list:
        return
    # 按创建时间排序
    tobe_list = sorted(tobe_list, key=lambda x: os.path.getctime(os.path.join(current_job_path, x)))
    new_list = tobe_list[0:adds]
    for j in new_list:
        update_job(os.path.join(current_job_path, j), new_status)
        log.info(f"commit job->{new_status}: {j}")


def run_job():
    """ 执行job(并发任务个数限制在max_number_job)
    """
    run_list = os.listdir(job_path_running)
    if not run_list:
        return

    # 当前运行job进程
    p_list = list()
    for p in multiprocessing.active_children():
        if f'agent@' in p.name:
            p_list.append(f"{p.name.replace(f'agent@', '')}.json")

    # running/下的任务状态: 没有运行的agent都跑
    tobe_list = list()
    for j in run_list:
        # 执行中的
        if j in p_list:
            continue

        j_file = os.path.join(job_path_running, j)
        j_id = j.replace('.json', '')
        tobe_list.append(multiprocessing.Process(target=Agent(j_file).run, name=f"agent@{j_id}", daemon=False))

    for p in tobe_list:
        p.start()
        log.info(f"agent process(pid={p.pid},name={p.name}) started")


def stop_job():
    """ 取消/停止任务
    """
    stop_list = os.listdir(job_path_stop)
    if not stop_list:
        return

    for stop_j in stop_list:
        j_file = check_job(stop_j.replace('.json', ''))

        os.remove(os.path.join(job_path_stop, stop_j))

        if j_file is None:
            return (False, 'job not found!')

        with open(j_file, 'r', encoding='utf-8') as f:
            j_info = json.loads(f.read())

        j_status = j_info['status']
        if j_status in (JOB_STATUS_DONE, JOB_STATUS_STOP, JOB_STATUS_TMOUT):
            return (True, 'job stopped already!')

        if j_status == JOB_STATUS_RUN:
            for p in multiprocessing.active_children():
                if f'agent@' in p.name:
                    log.info(f"stopping agent process(name={p.name},pid={p.pid})")
                    os.kill(p.pid, signal.SIGTERM)
            if f'win32' == sys.platform and j_info['pid'] != '':
                subprocess.run(f"taskkill /F /T /PID {j_info['pid']}")

        success, _ = update_job(j_file, JOB_STATUS_STOP)
        if success:
            log.info(f"job_id={j_info['id']} stopped success!")
        else:
            log.error(f"job_id={j_info['id']} stopped failed!")


def schedule_start():
    """ scheduler主程序
    """
    while True:
        commit_jobs(f'waiting')
        commit_jobs(f'running')
        run_job()
        stop_job()
        time.sleep(0.1)


def schedule_stop():
    """ scheduler主程序退出
    """
    p_list = list()
    for p in multiprocessing.active_children():
        log.info(f"process child: {p.name}")
        if p.name == f'scheduler':
            os.kill(p.pid, signal.SIGTERM)
            p_list.append(f"scheduler-{p.pid}")
            log.info(f"scheduler service(pid={p.pid}) stopped")
    return p_list


def schedule_status():
    """ scheduler主程序运行状态
    """
    p_list = list()
    for p in multiprocessing.active_children():
        if p.name == f'scheduler':
            p_list.append(f"scheduler-{p.pid}")
    return p_list


if not init():
    log.error("init failed!")
    exit(1)


worker_app = Flask(__name__)


@worker_app.route('/', methods=['GET'])
def hello():
    return f"Hello, this is the worker app at {api_info.worker_ip}:{api_info.worker_port}"


@worker_app.route('/job/new', methods=['POST'])
def service_new_job():
    if auth(request.headers):
        data = request.json
        job_info = data.get('job')
        success, message = new_job(job_info)
        if success:
            return json.dumps({
                "code": 200,
                "success": 'true',
                "message": "create job success!"
            })
        else:
            return json.dumps({
                "code": 200,
                "success": 'false',
                "message": message
            })
    else:
        return json.dumps({
            "code": 400,
            "success": 'false',
            "message": "invalid request!"
        })


@worker_app.route('/job/stop', methods=['POST'])
def service_new_stop_job():
    if auth(request.headers):
        data = request.json
        job_info = data.get('job')
        success, message = new_stop_job(job_info)
        if success:
            return json.dumps({
                "code": 200,
                "success": 'true',
                "message": "commit stopping-job success!",
                "result": {
                    "job": {
                        "id": job_info['id']
                    }
                }
            })
        else:
            return json.dumps({
                "code": 200,
                "success": 'false',
                "message": "commit stopping-job failed!",
                "result": {
                    "job": {
                        "id": job_info['id']
                    }
                }
            })
    else:
        return json.dumps({
            "code": 400,
            "success": 'false',
            "message": "invalid request!"
        })


@worker_app.route('/job/query', methods=['GET'])
def service_query_job():
    if auth(request.headers):
        job_id = request.args.get('jobId')
        success, message, job_info = query_job(job_id)
        if success:
            return json.dumps({
                "code": 200,
                "success": "true",
                "message": message,
                "result": {
                    "job": job_info
                }
            })
        else:
            return json.dumps({
                "code": 200,
                "success": "false",
                "message": message,
                "result": {
                    "job": job_info
                }
            })
    else:
        return json.dumps({
            "code": 400,
            "success": 'false',
            "message": "invalid request!"
        })


@worker_app.route('/schedule/start', methods=['POST'])
def service_start():
    if auth(request.headers, f'schedule'):
        for p in multiprocessing.active_children():
            log.info(f"process child: {p.name}")
            if p.name == f'scheduler':
                return json.dumps({
                    "code": "200",
                    "success": "false",
                    "message": f"scheduler exists(pid={p.pid})!"
                })
        p = multiprocessing.Process(target=schedule_start, daemon=False, name='scheduler')
        p.start()
        log.info(f"schedule service(pid={p.pid}) started")
        return json.dumps({
            "code": 200,
            "success": "true",
            "message": f"scheduler start(pid={p.pid}) success"
        })
    else:
        return json.dumps({
            "code": 400,
            "success": 'false',
            "message": "invalid request!"
        })


@worker_app.route('/schedule/stop', methods=['POST'])
def service_stop():
    if auth(request.headers, f'schedule'):
        p_list = schedule_stop()
        if 0 != len(p_list):
            return json.dumps({
                "code": 200,
                "success": "true",
                "message": f"stop scheduler({p_list}) success"
            })
        else:
            return json.dumps({
                "code": 200,
                "success": "false",
                "message": f"scheduler({p_list}) not running"
            })
    else:
        return json.dumps({
            "code": 400,
            "success": 'false',
            "message": "invalid request!"
        })


@worker_app.route('/schedule/status', methods=['GET'])
def service_detect():
    if auth(request.headers, f'schedule'):
        p_list = schedule_status()
        if p_list:
            return json.dumps({
                "code": 200,
                "success": "true",
                "message": f"scheduler({p_list}) alive"
            })
        else:
            return json.dumps({
                "code": 200,
                "success": "true",
                "message": f"scheduler({p_list}) not alive"
            })
        return json.dumps({
            "code": 200,
            "success": "false",
            "message": "scheduler not running!"
        })
    else:
        return json.dumps({
            "code": 400,
            "success": 'false',
            "message": "invalid request!"
        })


if __name__ == '__main__':
    log.info(f"worker app running(pid={os.getpid()})")
    http_server = WSGIServer((api_info.worker_ip, api_info.worker_port), worker_app)
    http_server.serve_forever()
