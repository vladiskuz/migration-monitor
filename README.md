# Live migration monitor

Since `easy_install` fails to setup the `libvirt`, run either `apt-get` or `pip` to install libvirt binding for python:

    (venv)$  pip install libvirt-python
    $ sudo apt-get install python-libvirt
    
Edit `settings.py`.
Then:

    (venv)$ python setup.py develop
    (venv)$ migrationmonitor
