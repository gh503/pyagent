#!/usr/bin/env python3
# coding: utf-8


import sys
import os
import yaml

lib_path = os.path.dirname(os.path.abspath(__file__))
if lib_path not in sys.path:
    sys.path.append(lib_path)


class CronJob:
    """ 本地定时任务。enable为开关。
    """

    def __init__(self, job_info_yaml):
        conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Conf')
        api_yaml = os.path.join(conf_path, job_info_yaml)

        with open(api_yaml, 'r', encoding='utf-8') as f:
            jobs = yaml.safe_load(f.read())

        # KeyError直接触发异常，当前指定任务执行失败
        self.job_info = jobs[job_name]

    def run(self):
        """ 执行任务
        """
        pass
