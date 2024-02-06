#!/usr/bin/env python3
# coding: utf-8


import requests
import json
import yaml
import sys
import urllib.parse
import copy


def start(job_info: dict)->bool:

   url = "http://127.0.0.1:8080/job/new"
   payload = json.dumps({"job": job_info})
   headers = {
      'User-Agent': 'Apifox/1.0.0 (https://www.apifox.cn)',
      'Content-Type': 'application/json',
      'Accept': '*/*',
      'Host': '0.0.0.0:8080',
      'Connection': 'keep-alive',
      "username": "username",
      "password": "password",
   }

   response = requests.request("POST", url, headers=headers, data=payload)

   print(response.text)


def query(job_info: dict)->bool:

   url = "http://127.0.0.1:8080/job/query"

   params = {
      "jobId": job_info['id']
   }
   if params is not None and len(params) != 0:
       full_url = url + '?' + urllib.parse.urlencode(params)
   else:
       full_url = url

   headers = {
      'User-Agent': 'Apifox/1.0.0 (https://www.apifox.cn)',
      'Content-Type': 'application/json',
      'Accept': '*/*',
      'Host': '0.0.0.0:8080',
      'Connection': 'keep-alive',
      "username": "username",
      "password": "password",
   }

   response = requests.request("GET", full_url, headers=headers)

   print(response.text)


def stop(job_info: dict)->bool:

   url = "http://127.0.0.1:8080/job/stop"

   payload = json.dumps({
      "job": {
         "id": job_info['id']
      }
   })
   headers = {
      'User-Agent': 'Apifox/1.0.0 (https://www.apifox.cn)',
      'Content-Type': 'application/json',
      'Accept': '*/*',
      'Host': '0.0.0.0:8080',
      'Connection': 'keep-alive',
      "username": "username",
      "password": "password",
   }

   response = requests.request("POST", url, headers=headers, data=payload)

   print(response.text)


with open(f'test.yaml', 'r', encoding='utf-8') as f:
   config = yaml.safe_load(f)

jobs = config['job']
for job in copy.deepcopy(jobs):
   if f'enable' in job.keys() and not job['enable']:
      jobs.remove(job)

# print(jobs)

if len(sys.argv) != 2:
   exit(1)

action = sys.argv[1]
if action == f'query':
   for job in jobs:
      query(job)

elif action == f'stop':
   for job in jobs:
      stop(job)

elif action == f'start':
   for job in jobs:
      start(job)

else:
   print(f'unsupported action {action}')
   exit(2)
