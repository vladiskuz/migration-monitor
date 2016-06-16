# Live migration monitor

Since `easy_install` fails to setup the `libvirt`, run either `apt-get` or `pip` to install libvirt binding for python:

    (venv)$  pip install libvirt-python
    $ sudo apt-get install python-libvirt

Edit `settings.py`.
Then:

    (venv)$ python setup.py develop
    (venv)$ migrationmonitor

In vagrant:
	
	$ wget https://cloud-images.ubuntu.com/trusty/20160610/trusty-server-cloudimg-amd64-disk1.img

    $ virt-install --connect qemu:///system -n cirros_1 -r 256 --os-type=linux --disk path=~/cirros-0.3.0-x86_64-disk.img,device=disk,format=qcow2 --vcpus=1 --noautoconsole --import

    $ virsh migrate --live cirros_1 qemu+tcp://node1/system

    $ virsh -c qemu+tcp://node1/system migrate --live cirros_1 qemu+tcp://node2/system

This would be great, but it's not working for NFS shares (like /vagrant)

    _$ watchmedo shell-command --patterns="\*.py" --recursive --command="~/.venv/bin/migrationmonitor"_
