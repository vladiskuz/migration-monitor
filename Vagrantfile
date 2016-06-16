# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/wily64"

  # config.vm.network "private_network", type: "dhcp"

  config.vm.provider "libvirt" do |lv|
    lv.memory = "2048"
  end

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end
  
  config.hostmanager.enabled = true
  config.hostmanager.manage_guest = true
  # config.hostmanager.manage_host = true
  config.hostmanager.ignore_private_ip = false

  config.vm.define "node1" do |node|
    node.vm.hostname = "node1"
    node.vm.network :private_network, ip: '192.168.42.11'
  end

  config.vm.define "node2" do |node|
    node.vm.hostname = "node2"
    node.vm.network :private_network, ip: '192.168.42.12'
  end

  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get install -y htop qemu libvirt-bin libvirt-dev python-dev python-virtualenv virtinst emacs python-libvirt
    sudo apt-get purge -qq -y --auto-remove chef puppet

    sudo sed -i 's|#listen_tls = 0|listen_tls = 0|' /etc/libvirt/libvirtd.conf
    sudo sed -i 's|#listen_tcp = 1|listen_tcp = 1|' /etc/libvirt/libvirtd.conf
    sudo sed -i 's|#auth_tcp = "sasl"|auth_tcp="none"|' /etc/libvirt/libvirtd.conf

    sudo sed -i 's|env libvirtd_opts="-d"|env libvirtd_opts="-d -l"|' /etc/init/libvirt-bin.conf
    sudo sed -i 's|libvirtd_opts="-d"|libvirtd_opts="-d -l"|' /etc/default/libvirt-bin

    sudo service libvirt-bin restart
    wget https://launchpad.net/cirros/trunk/0.3.0/+download/cirros-0.3.0-x86_64-disk.img

    sudo usermod -a -G libvirtd vagrant

    virtualenv ~/.venv
    ~/.venv/bin/pip install libvirt-python
    ~/.venv/bin/python /vagrant/setup.py develop

    sudo pip install watchdog
  SHELL
  # config.vm.provision :ansible do |ansible|
  #   # ansible.playbook = "ansible/start.yml"
  # end
end
