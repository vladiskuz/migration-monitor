# Live migration monitor

Since `easy_install` fails to setup the `libvirt`, run either `apt-get` or `pip` to install libvirt binding for python:

    (venv)$  pip install libvirt-python
    
    $ sudo apt-get install python-libvirt
    
Then:

    $ python setup.py develop
