# Live migration monitor

[![Build Status](https://travis-ci.org/rk4n/migration-monitor.svg?branch=master)](https://travis-ci.org/rk4n/migration-monitor)

Since `easy_install` fails to setup the `libvirt`, run either `apt-get` or `pip` to install libvirt binding for python:

    (venv)$  pip install libvirt-python

or

    $ sudo apt-get install python-libvirt


Create and edit `settings.py`:

    $ cp settings.py.template settings.py

then:

    (venv)$ python setup.py develop
    (venv)$ migrationmonitor
