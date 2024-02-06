#!/usr/bin/env python3
# coding: utf-8
#
# 采集worker机信息并输出到终端(windows/linux)


import platform
import subprocess
import re


OS = platform.system()

if OS != 'Windows' and OS != 'Linux':
    print("unsupported os type:", OS)
    exit(1)


info = {'os_type': OS}


def executeHostCmd(cmd: str, timeoutSec: int=10):
    completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                        timeout=timeoutSec, check=False, encoding='utf-8')
    return (completed_process.returncode, completed_process.stdout)


class Win32Info:
    """ windows系统信息采集类
    """

    def __init__(self):
        self.__get_systeminfo()
        self.__get_cpu_cores()
        self.__get_logical_processors()
        self.__get_memory_size()
        self.__get_disk_size()
        self.__get_ipv4_address()

    def __get_systeminfo(self):

        info['os_arch'] = 'unknown'
        info['os_version'] = 'unknown'
        info['os_name'] = 'unknown'
        info['cpu_sockets'] = 'unknown'

        code, result = executeHostCmd(f'chcp 65001 && systeminfo')
        if 0 != code:
            return

        if f'x64-based PC' in result:
            info['os_arch'] = 'x86_64'
            
        test = re.search('OS Version:\s+(.*)', result)
        if test is not None:
            info['os_version'] = test.group(1)

        test = re.search('OS Name:\s+(.*)', result)
        if test is not None:
            info['os_name'] = test.group(1)

        test = re.search('(\d+)\s+Processor\(s\) Installed', result)
        if test is not None:
            info['cpu_sockets'] = test.group(1)

    def __get_cpu_cores(self):

        info['cpu_cores'] = 'unknown'

        code, result = executeHostCmd(f'wmic cpu get NumberOfCores')
        if 0 != code:
            return

        test = re.search('\d+', result)
        if test is not None:
            info['cpu_cores'] = test.group(0)

    def __get_logical_processors(self):

        info['cpu_logic'] = 'unknown'

        code, result = executeHostCmd(f'wmic cpu get NumberOfLogicalProcessors')
        if 0 != code:
            return

        test = re.search('\d+', result)
        if test is not None:
            info['cpu_logic'] = test.group(0)

    def __get_memory_size(self):

        info['memory_size'] = 'unknown'

        code, result = executeHostCmd(f'wmic memorychip get Capacity')
        if 0 != code:
            return

        test = re.findall('\d+', result)
        if test is not None:
            total = 0
            for m in test:
                total += int(m)
            info['memory_size'] = "{}GB".format(int(total/1024/1024/1024))

    def __get_disk_size(self):

        info['disk_size'] = 'unknown'

        code, result = executeHostCmd(f"wmic volume get Capacity,Caption")
        if 0 != code:
            return

        test = re.findall('(\d+)\s+([A-Z]:)', result)
        if test is not None:
            info['disk_size'] = ''
            for e in test:
                a = e[1]
                b = int(int(e[0])/1024/1024/1024)
                info['disk_size'] += f'{a} {b}GB '
            info['disk_size'] = info['disk_size'].strip()

    def __get_ipv4_address(self):

        info['ipv4_address'] = 'unknown'

        code, result = executeHostCmd(f'route print -4 | findstr 0.0.0.0')
        if 0 != code:
            return

        test = re.match('\s+0.0.0.0\s+0.0.0.0\s+\d+.\d+.\d+.\d+\s+(\d+.\d+.\d+.\d+)', result)
        if test is not None:
            info['ipv4_address'] = test.group(1)


class LinuxInfo:
    """ linux系统信息采集类
    """

    def __init__(self):
        self.__get_os_arch()
        self.__get_os_version()
        self.__get_os_name()
        self.__get_cpu_sockets()
        self.__get_cpu_cores()
        self.__get_logical_processors()
        self.__get_memory_size()
        self.__get_disk_size()
        self.__get_ipv4_address()

    def __get_os_arch(self):
        code, result = executeHostCmd(f'arch')
        if 0 == code:
            info['os_arch'] = result.replace('\n', '')
        else:
            info['os_arch'] = 'unknown'
        
    def __get_os_version(self):
        code, result = executeHostCmd('. /etc/os-release && echo ${VERSION}')
        if 0 == code:
            info['os_version'] = result.replace('\n', '')
        else:
            info['os_version'] = 'unknown'
        
    def __get_os_name(self):
        code, result = executeHostCmd('. /etc/os-release && echo ${NAME}')
        if 0 == code:
            info['os_name'] = result.replace('\n', '')
        else:
            info['os_name'] = 'unknown'
        
    def __get_cpu_sockets(self):
        code, result = executeHostCmd("grep 'physical id' /proc/cpuinfo | uniq | wc -l")
        if 0 == code:
            info['cpu_sockets'] = result.replace('\n', '')
        else:
            info['cpu_sockets'] = 'unknown'
        
    def __get_cpu_cores(self):
        code, result = executeHostCmd("grep -c 'cpu cores' /proc/cpuinfo")
        if 0 == code:
            info['cpu_cores'] = result.replace('\n', '')
        else:
            info['cpu_cores'] = 'unknown'

    def __get_logical_processors(self):
        code, result = executeHostCmd("grep -c processor /proc/cpuinfo")
        if 0 == code:
            info['cpu_logic'] = result.replace('\n', '')
        else:
            info['cpu_logic'] = 'unknown'
        
    def __get_memory_size(self):
        code, result = executeHostCmd('free -gt | grep Total | awk \'{print $2;exit}\'')
        if 0 == code:
            info['memory_size'] = result.replace('\n', '') + "GB"
        else:
            info['memory_size'] = 'unknown'
    
    def __get_disk_size(self):
        code, result = executeHostCmd('lsblk | grep disk | awk \'{print $1,$4}\'')
        if 0 == code:
            info['disk_size'] = result.replace('\n', '')
        else:
            info['disk_size'] = 'unknown'

    def __get_ipv4_address(self):
        code, result = executeHostCmd('ip route get 1.2.3.4 | awk \'{print $7;exit}\'')
        if 0 == code:
            info['ipv4_address'] = result.replace('\n', '')
        else:
            info['ipv4_address'] = 'unknown'


if f'Windows' == OS:
    Win32Info()
else:
    LinuxInfo()

print(info)
