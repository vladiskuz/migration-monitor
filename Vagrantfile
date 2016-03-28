# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/trusty64"
  # config.vm.network "private_network", type: "dhcp"
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
  
  # config.vm.provision "shell", inline: <<-SHELL
  #   sudo apt-get update
  #   sudo apt-get install -y htop qemu libvirt-bin libvirt-dev python-dev python-virtualenv virtinst
  #   sudo apt-get purge -qq -y --auto-remove chef puppet
  # SHELL
  config.vm.provision :ansible do |ansible|
    ansible.playbook = "ansible/site.yml"
    # ansible.playbook = "ansible/stop.yml"
  end
end
