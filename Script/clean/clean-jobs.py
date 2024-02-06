#!/usr/bin/env python3
# coding: utf-8
#
# 清理worker机workspace目录下的垃圾

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Lib'))
from tlog import Tlog

log = Tlog()
log.print('aaaa')
log.debug('aaaa')
log.info('bbbb')
log.warn('cccc')
log.error('ddddd')
