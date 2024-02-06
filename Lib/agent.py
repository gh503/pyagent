#!/usr/bin/env python3
# coding: utf-8

import sys
import os
import json
import datetime
import subprocess
import signal
import time

lib_path = os.path.dirname(os.path.abspath(__file__))
if lib_path not in sys.path:
    sys.path.append(lib_path)

from tlog import Tlog, LOG_LEVEL_INFO
from restful import api_info

JOB_STATUS_NEW, JOB_STATUS_WAIT, JOB_STATUS_RUN, JOB_STATUS_TMOUT, JOB_STATUS_DONE, JOB_STATUS_STOP = \
    f'created', f'waiting', f'running', f'timeout', f'finished', f'stopped'
JOB_RESULT_SUCC, JOB_RESULT_FAIL = f'success', f'failed'


class Agent:
    """ 处置running/下的job
    """
    # 上报周期
    report_seconds = 15
    # 重跑次数
    max_retry_times = 3


    def __init__(self, job_info_json):

        if f'win32' == sys.platform:
            subprocess.run("chcp 65001", shell=True, stdout=subprocess.DEVNULL)

        with open(job_info_json, 'r', encoding='utf-8') as f:
            job_info = json.loads(f.read(), encoding='utf-8')

        taskId, taskTimeStamp, _ = job_info['id'].split('-')
        job_info['workspace'] = os.path.join(api_info.worker_workspace, taskId, taskTimeStamp)
        job_info['log'] = os.path.join(job_info['workspace'], 'task.log')

        if not os.path.isdir(job_info['workspace']):
            os.makedirs(job_info['workspace'])

        self.log = Tlog(level=LOG_LEVEL_INFO, log_file=job_info['log'])
        self.job_info_json = job_info_json
        self.job_info = job_info

        self.log.info("任务agent初始化...")
        self.job_info['ppid'] = os.getpid()

        if f'timeoutSec' not in self.job_info.keys():
            self.job_info['timeoutSec'] = 0  # 0 表示不超时

        if f'retry' in self.job_info.keys():
            self.job_info['retry'] += 1
        else:
            self.job_info['retry'] = 0

        # 非running状态
        if job_info['status'] != JOB_STATUS_RUN:
            self.log.warn(f"Job status={job_info['status']} NOT {JOB_STATUS_RUN}, remove job directly:\n{job_info}\n")
            self.update_job_json(f'done')
            return

        # 重跑次数过多
        if f'retry' in job_info.keys() and job_info['retry'] >= Agent.max_retry_times:
            self.log.warn(f"Job retry={job_info['retry']} >= {Agent.max_retry_times} failed too many times, remove job directly:\n{job_info}\n")
            self.update_job_json(f'done')
            return

        self.log.info(f"agent开始执行任务: {self.job_info_json}\n{self.job_info}\n")
        self.before()


    def report(self):
        """ agent上报任务数据
        """
        api = api_info.serverApi['report']
        api['header'].update({
                "username": api_info.worker_username,
                "password": api_info.worker_password,
        })

        data = {"job": self.job_info}
        response = api_info.request(api['url'],
                                    api['header'],
                                    api['param'],
                                    api['body'],
                                    api['method'],
                                    data)
        success, _ = api_info.check_response(api['expected'], response)
        if not success:
            self.log.error(f"agent上报任务数据异常: {api['url']}\n{response['message']}\n")


    def update_job_json(self, new_layer):
        if new_layer not in ('running', 'done'):
            self.log.error(f"agent更新任务json参数异常: new_layer expected 'running' or 'done'\n")
            return

        try:
            os.remove(self.job_info_json)
            dir_json_new = os.path.realpath(os.path.join(os.path.dirname(self.job_info_json), '..', new_layer))
            if not os.path.isdir(dir_json_new):
                os.makedirs(dir_json_new)
            job_info_json_new = os.path.join(dir_json_new, os.path.basename(self.job_info_json))
            with open(job_info_json_new, 'w', encoding='utf-8') as f:
                f.write(json.dumps(self.job_info))

            self.job_info_json = job_info_json_new

            self.report()

        except Exception as e:
            self.log.error(f"agent更新任务json异常: {str(e)}\n{self.job_info_json}\n{self.job_info}\n")


    def before(self):
        self.log.info("[before] agent开始任务执行前动作...")
        self.job_info['start'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.job_info['return'] = ""
        self.job_info['pid'] = ''
        self.process = None
        if not os.path.isdir(self.job_info['workspace']):
            os.makedirs(self.job_info['workspace'])

        # 使用临时脚本执行
        if f'win32' == sys.platform:
            cmd_script = os.path.join(self.job_info['workspace'], f"{self.job_info['id']}.bat")
            cmd_run = cmd_script
        else:
            cmd_script = os.path.join(self.job_info['workspace'], f"{self.job_info['id']}.sh")
            cmd_run = f"sh {cmd_script}"

        with open(cmd_script, 'w', encoding='utf-8') as f:
            f.write(self.job_info['cmd'])

        self.job_info['cmd_script'] = cmd_script
        self.job_info['cmd_run'] = cmd_run

        self.update_job_json(f'running')
        self.log.info(f"[before] agent完成任务执行前动作: {self.job_info_json}\n{self.job_info}\n")


    def after(self):
        self.log.info("[after] agent开始任务执行后动作...")
        self.job_info['realEnd'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.job_info['code'] = self.process.poll()
        self.process = None
        # 超时运行失败 -signal
        if self.job_info['status'] == JOB_STATUS_TMOUT:
            self.job_info['result'] = JOB_RESULT_FAIL
            self.log.error("任务超时，运行失败!\n")
        # 未超时(完成 + 成功 code==0)
        elif 0 == self.job_info['code']:
            self.job_info['result'] = JOB_RESULT_SUCC
            self.job_info['status'] = JOB_STATUS_DONE
            self.log.info("任务结束，运行成功!\n")
        # 未超时(完成 + 失败 code>0)
        elif 0 < self.job_info['code']:
            self.job_info['result'] = JOB_RESULT_FAIL
            self.job_info['status'] = JOB_STATUS_DONE
            self.log.error("任务结束，运行失败!\n")
        # 未超时(未完成 + 失败 -signalN code<0)
        else:
            self.job_info['result'] = JOB_RESULT_FAIL
            self.job_info['status'] = JOB_STATUS_STOP
            self.log.error("任务暂停，运行失败!\n")
        self.job_info['end'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.update_job_json(f'done')
        self.log.info(f"[after] agent完成任务执行后动作: {self.job_info_json}\n{self.job_info}\n")


    def run(self):
        """ 执行子任务(直到结束)
        """
        self.log.info("[run] agent开始执行任务...")

        signal.signal(signal.SIGTERM, self.stop)

        report_times = 0
        realStart = datetime.datetime.now()
        self.job_info['realStart'] = realStart.strftime("%Y-%m-%d %H:%M:%S")
        log_fh = open(self.job_info['log'], 'a+')
        self.process = subprocess.Popen(self.job_info['cmd_run'],
                                   cwd=self.job_info['workspace'],
                                   shell=True, close_fds=True,
                                   stdout=log_fh,  # 配合readline非阻塞处理
                                   stderr=subprocess.STDOUT,
                                   encoding='utf-8'  # 直接解码byte为text
                                   )
        self.job_info['pid'] = self.process.pid
        self.update_job_json(f'running')
        while self.process.poll() is None:
            # ref: https://www.vksir.zone/posts/subprocess/
            # readline遇到EOF返回，配合文件不阻塞，如果用Pipe会阻塞
            line = log_fh.readline().strip()
            if line:
                self.job_info['return'] += line

            # 定时上报
            now = datetime.datetime.now()
            secCost = (now - realStart).seconds
            if secCost > (report_times + 1)*Agent.report_seconds:
                self.update_job_json(f'running')
                report_times += 1

            # 超时终结
            if 0 != self.job_info['timeoutSec'] and secCost >= self.job_info['timeoutSec']:
                self.process.terminate()
                self.process.wait()
                self.job_info['status'] = JOB_STATUS_TMOUT
                break

            # 日志实时
            log_fh.flush()
            time.sleep(0.1)
        log_fh.close()
        self.log.info(f"[run] agent完成执行任务: {self.job_info_json}\n{self.job_info}\n")

        self.after()


    def stop(self):
        if self.process:
            self.log.info(f"[stop] agent开始停止执行任务...")
            self.log.info(f"stopping command process(pid={self.process.pid})")
            self.process.terminate()
            self.process.wait()
            self.job_info['status'] = JOB_STATUS_TMOUT
            self.log.info(f"[stop] agent完成停止执行任务: {self.job_info_json}\n{self.job_info}\n")

            self.after()
