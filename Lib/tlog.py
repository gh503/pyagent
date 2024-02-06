#!/usr/bin/env python3
# coding: utf-8


from sys import stdout, stderr
from datetime import datetime


# Foreground Colors
BLACK = "\033[0;30m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN = "\033[0;36m"
WHITE = "\033[0;37m"

LIGHT_BLACK = "\033[1;30m"
LIGHT_RED = "\033[1;31m"
LIGHT_GREEN = "\033[1;32m"
LIGHT_YELLOW = "\033[1;33m"
LIGHT_BLUE = "\033[1;34m"
LIGHT_MAGENTA = "\033[1;35m"
LIGHT_CYAN = "\033[1;36m"
LIGHT_WHITE = "\033[1;37m"

# Background Colors
BLACK_BG = "\033[0;40m"
RED_BG = "\033[0;41m"
GREEN_BG = "\033[0;42m"
YELLOW_BG = "\033[0;43m"
BLUE_BG = "\033[0;44m"
MAGENTA_BG = "\033[0;45m"
CYAN_BG = "\033[0;46m"
WHITE_BG = "\033[0;47m"

LIGHT_BLACK_BG = "\033[1;40m"
LIGHT_RED_BG = "\033[1;41m"
LIGHT_GREEN_BG = "\033[1;42m"
LIGHT_YELLOW_BG = "\033[1;43m"
LIGHT_BLUE_BG = "\033[1;44m"
LIGHT_MAGENTA_BG = "\033[1;45m"
LIGHT_CYAN_BG = "\033[1;46m"
LIGHT_WHITE_BG = "\033[1;47m"

# Special Codes
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
RESET = "\033[0m"


LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARN, LOG_LEVEL_ERR = f'debug', f'info', f'warn', f'error'


class Tlog:


    def __init__(self, level: str=LOG_LEVEL_INFO, log_file=None):
        self.log_level = level
        self.log_file = log_file

        if not self.log_level:
            self.log_level = LOG_LEVEL_INFO

        if self.log_level not in (LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARN, LOG_LEVEL_ERR):
            raise Exception("Tlog level set error!")


    def setloglevel(self, level: str=LOG_LEVEL_INFO)->bool:
        """ 设置日志级别
        """
        if level not in (LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARN, LOG_LEVEL_ERR):
            self.terror('setloglevel failed!')
            return False

        self.log_level = level


    def setlogfile(self, log_file=None):
        """ 设置日志输出端，默认None
        """
        if log_file:
            self.log_file = log_file


    def print(self, msg: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.log_file:
            with open(self.log_file, 'a+', encoding='utf-8') as f:
                print('{} {}'.format(now, msg), file=f)
        else:
            print('{} {}'.format(now, msg), file=stdout)


    def debug(self, msg: str):
        if self.log_level not in (LOG_LEVEL_DEBUG,):
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.log_file:
            with open(self.log_file, 'a+', encoding='utf-8') as f:
                print('[{}][{}{}{}] {}'.format(now, LIGHT_MAGENTA, 'DEBUG', RESET, msg), file=f)
        else:
            print('[{}][{}{}{}] {}'.format(now, LIGHT_MAGENTA, 'DEBUG', RESET, msg), file=stdout)


    def info(self, msg: str):
        if self.log_level not in (LOG_LEVEL_DEBUG, LOG_LEVEL_INFO):
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.log_file:
            with open(self.log_file, 'a+', encoding='utf-8') as f:
                print('[{}][{}{}{}] {}'.format(now, LIGHT_GREEN, 'INFO ', RESET, msg), file=f)
        else:
            print('[{}][{}{}{}] {}'.format(now, LIGHT_GREEN, 'INFO ', RESET, msg), file=stdout)


    def warn(self, msg: str):
        if self.log_level not in (LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARN):
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.log_file:
            with open(self.log_file, 'a+', encoding='utf-8') as f:
                print('[{}][{}{}{}] {}'.format(now, LIGHT_YELLOW, 'WARN ', RESET, msg), file=f)
        else:
            print('[{}][{}{}{}] {}'.format(now, LIGHT_YELLOW, 'WARN ', RESET, msg), file=stdout)


    def error(self, msg: str):
        if self.log_level not in (LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARN, LOG_LEVEL_ERR):
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.log_file:
            with open(self.log_file, 'a+', encoding='utf-8') as f:
                print('[{}][{}{}{}] {}'.format(now, LIGHT_RED, 'ERROR', RESET, msg), file=f)
        else:
            print('[{}][{}{}{}] {}'.format(now, LIGHT_RED, 'ERROR', RESET, msg), file=stderr)
