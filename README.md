# Live migration monitor

[![Build Status](https://travis-ci.org/rk4n/migration-monitor.svg?branch=master)](https://travis-ci.org/rk4n/migration-monitor)

Since `easy_install` fails to setup the `libvirt`, run either `apt-get` or `pip` to install libvirt binding for python:

    (venv)$  pip install libvirt-python
    $ sudo apt-get install python-libvirt

Edit `settings.py`.
Then:

    (venv)$ python setup.py develop
    (venv)$ migrationmonitor

In vagrant:
	
	$ wget https://cloud-images.ubuntu.com/trusty/20160610/trusty-server-cloudimg-amd64-disk1.img

    $ virt-install --connect qemu:///system -n ubu_1 -r 256 --vcpus=1 --noautoconsole --import --os-type=linux \
         --disk path=~/trusty-server-cloudimg-amd64-disk1.img,device=disk,format=qcow2 \
         --disk path=/vagrant/cloud-config/config.iso,device=cdrom


    $ virsh migrate --live cirros_1 qemu+tcp://node1/system

    $ virsh -c qemu+tcp://node1/system migrate --live cirros_1 qemu+tcp://node2/system

This would be great, but it's not working for NFS shares (like /vagrant)

    _$ watchmedo shell-command --patterns="\*.py" --recursive --command="~/.venv/bin/migrationmonitor"_
