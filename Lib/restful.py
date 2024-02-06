#!/usr/bin/env python3
# coding: utf-8


import sys
import os
import re
import copy
import yaml
import json
import urllib.parse
import urllib.request
import urllib.error
import multiprocessing

lib_path = os.path.dirname(os.path.abspath(__file__))
if lib_path not in sys.path:
    sys.path.append(lib_path)

from tlog import Tlog

log = Tlog()


class Api:
    """ 此类为Api实体类。解析api.yaml，并生成基础AW：请求与校验响应。
    """

    def __init__(self, api_yaml_file='api.yaml'):
        """ 实例解析api.yaml，失败后直接触发异常。
        """
        main_path = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        conf_path = os.path.join(main_path, 'Conf')
        api_yaml = os.path.join(conf_path, api_yaml_file)

        with open(api_yaml, 'r', encoding='utf-8') as f:
            api_settings = yaml.safe_load(f.read())

        server_settings = api_settings['server']
        server_url = server_settings['url']
        self.server_username = server_settings['username']
        self.server_password = server_settings['password']
        self.serverApi = {"report": {}}
        for api in self.serverApi.keys():
            self.serverApi[api]['url'] = server_url + server_settings[api]['url']
            self.serverApi[api]['method'] = server_settings[api]['method']
            self.serverApi[api]['header'] = server_settings[api]['header']
            self.serverApi[api]['param'] = server_settings[api]['param']
            self.serverApi[api]['body'] = server_settings[api]['body']
            self.serverApi[api]['expected'] = server_settings[api]['expected']

        worker_settings = api_settings['worker']
        worker_url = worker_settings['url']
        self.worker_username = worker_settings['username']
        self.worker_password = worker_settings['password']
        test = re.search('\d+.\d+.\d+.\d+', worker_url)
        if test is not None:
            self.worker_ip = test.group(0)
        else:
            self.worker_ip = None
        test = re.search(':(\d+)', worker_url)
        if test is not None:
            self.worker_port = int(test.group(1))
        else:
            self.worker_port = None

        self.worker_workspace = worker_settings['workspace']
        if f'max_number_job' not in worker_settings.keys() or worker_settings['max_number_job'] is None:
            self.worker_parallel_jobs =  multiprocessing.cpu_count()
        else:
            self.worker_parallel_jobs =  worker_settings['max_number_job']
        self.worker_job_path = {
            "new": os.path.join(main_path, worker_settings['job']['path'], worker_settings['job']['new']),
            "wait": os.path.join(main_path, worker_settings['job']['path'], worker_settings['job']['wait']),
            "run": os.path.join(main_path, worker_settings['job']['path'], worker_settings['job']['run']),
            "done": os.path.join(main_path, worker_settings['job']['path'], worker_settings['job']['done']),
            "stop": os.path.join(main_path, worker_settings['job']['path'], worker_settings['job']['stop']),
        }
        self.workerApi = {"jobNew": {}, "jobStop": {}}
        for api in self.workerApi.keys():
            self.workerApi[api]['url'] = worker_url + worker_settings[api]['url']
            self.workerApi[api]['method'] = worker_settings[api]['method']
            self.workerApi[api]['header'] = worker_settings[api]['header']
            self.workerApi[api]['param'] = worker_settings[api]['param']
            self.workerApi[api]['body'] = worker_settings[api]['body']
            self.workerApi[api]['expected'] = worker_settings[api]['expected']


    def request(self, url: str, header: dict, param: dict,
                      body: dict, method: str, update: dict)->dict:
        """ 封装基础接口，提供业务API调用

        1.这里默认所有API响应为JSON数据处理，不支持其他类型响应;
        """
        if method in ('post', 'put') and body is None:
            log.terror(f"post/put request without body data: {url}")
            return

        try:
            if param is not None and len(param) != 0:
                full_url = url + '?' + urllib.parse.urlencode(param)
            else:
                full_url = url

            if header is None:
                header = {}

            data = None
            if body is not None and len(body) != 0:
                if len(update) != 0:
                    copy_body = copy.deepcopy(body)
                    for k in copy_body.keys():
                        if f'job' == k:
                            for k in copy_body['job'].keys():
                                if k in update['job'].keys():
                                    body["job"][k] = update['job'][k]
                                else:
                                    body["job"][k] = ''
                        else:
                            if k in update.keys():
                                body[k] = update[k]

                data = json.dumps(body).encode('utf-8')

            req = urllib.request.Request(full_url, headers=header, data=data)
            with urllib.request.urlopen(req) as f:
                return json.loads(f.read().decode('utf-8'), encoding='utf-8')

        except KeyError as e:
            log.terror(f"update api info failed: {full_url}\n{e}")
        # 优先处理HTTPError，URLError包括HTTPError
        except urllib.error.HTTPError as e:
            log.terror(f"server internal error: {e.code}-{full_url}\n{e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            log.terror(f"unreachable resource: {full_url}\n{e.reason}")
        except json.JSONDecodeError as e:
            log.terror(f"convert response to dict failed: {full_url}\n{e}")
        except Exception as e:
            log.terror(f"{full_url}\n{e}")


    def check_response(self, expected: dict, response: dict)->tuple:
        """ 校验API响应，并获取响应信息

        1.要求响应中所有的key不能重复
        """
        if not isinstance(response, dict) or 0 == len(response):
            return (False, None)

        output = dict()
        for k, v in expected.items():

            if k not in response.keys():
                return (False, None)

            if isinstance(v, dict):
                success, _output_ = self.check_response(v, response[k])
                if not success:
                    return (False, None)
                else:
                    # 这里不能有重复key
                    output.update(_output_)
            else:
                if v is not None and v != response[k]:
                    return (False, None)

                output[k] = response[k]

        return (True, output)

api_info = Api()
