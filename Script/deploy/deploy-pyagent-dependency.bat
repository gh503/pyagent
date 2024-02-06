@echo off

rem 默认python3/pip安装完成，且通过python命令可以执行python3解释器

python -m pip install  virtualenvwrapper-win

set virtualenv_name=worker-app-main
mkvirtualenv %virtualenv_name%
workon %virtualenv_name%

python -m pip install PyYAML Flask gevent colorama
