#!/bin/bash


python3 -m pip install virtualenvwrapper

virtualenv_name='worker-app-main'

mkvirtualenv ${virtualenv_name}
workon ${virtualenv_name}

python3 -m pip install PyYAML Flask gevent colorama
