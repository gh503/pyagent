#!/usr/bin/env python3
# coding: utf-8


import sys
import os
from datetime import datetime
import json
import subprocess
import time

lib_path = os.path.dirname(os.path.abspath(__file__))
if lib_path not in sys.path:
    sys.path.append(lib_path)

from job import Job


class Scene(Job):
    """ 具体场景任务。
    """

    def __init__(self, scene, job_info_json):
        super().__init__(job_info_json)
        self.scene = scene

class collect(Job):
    """ 采集任务。
    """

    def __init__(self):
        pass


class download(Job):
    """ 下载任务。
    """

    def __init__(self):
        pass


class build(Job):
    """ 编译任务
    """

    def __init__(self):
        pass


class install(Job):
    """ 安装任务
    """

    def __init__(self):
        pass


class test(Job):
    """ 测试任务。
    """

    def __init__(self):
        pass


class report(Job):
    """ 报告任务
    """

    def __init__(self):
        pass


class clean(Job):
    """ 清理任务。
    """

    def __init__(self):
        pass


class uninstall(Job):
    """ 卸载任务
    """

    def __init__(self):
        pass


class inform(Job):
    """ 通知任务
    """

    def __init__(self):
        pass
