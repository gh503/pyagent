#!/usr/bin/env python3
# coding: utf-8


import sys
import requests
import json

def get(action: str=None, job_id: str=None)->bool:

   url = f"http://127.0.0.1:8080/schedule/{action}"

   if action == f'queryJob':
      params = {
         "jobId": job_id
      }
   else:
      params = {}

   headers = {
      'User-Agent': 'Apifox/1.0.0 (https://www.apifox.cn)',
      'Content-Type': 'application/json',
      'Accept': '*/*',
      'Host': '127.0.0.1:8080',
      'Referer': '127.0.0.1:8080',
      'Connection': 'keep-alive',
      "username": "username",
      "password": "password",
   }

   response = requests.request("GET", url, params=params, headers=headers)

   print(response.text)


def post(action: str=None, job_id: str=None)->bool:

   url = f"http://127.0.0.1:8080/schedule/{action}"

   if action in ('stopJob', 'queryJob') and job_id:
      payload = json.dumps({
         "job": {
            "id": job_id
         }
      })
   else:
      payload = None

   headers = {
      'User-Agent': 'Apifox/1.0.0 (https://www.apifox.cn)',
      'Content-Type': 'application/json',
      'Accept': '*/*',
      'Host': '127.0.0.1:8080',
      'Referer': '127.0.0.1:8080',
      'Connection': 'keep-alive',
      "username": "username",
      "password": "password",
   }

   response = requests.request("POST", url, headers=headers, data=payload)

   print(response.text)


if len(sys.argv) != 2:
   exit(1)

action = sys.argv[1]
if action in ('start', 'stop'):
   post(action=action)
elif action in ('status',):
   get(action=action)
else:
   exit(2)
