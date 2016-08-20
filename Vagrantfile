# -*- mode: ruby -*-
# vi: set ft=ruby :

$main_script = <<SCRIPT
sudo echo "\n127.0.1.1 ubuntu-xenial\n" >> /etc/hosts
sudo add-apt-repository -y ppa:jacob/virtualisation

sudo apt-get update

sudo apt-get install -y htop qemu libvirt-bin \
libvirt-dev python-dev python-virtualenv python-pip \
virtinst emacs python-libvirt bridge-utils mc genisoimage


sudo sed -i 's|#listen_tls = 0|listen_tls = 0|' /etc/libvirt/libvirtd.conf
sudo sed -i 's|#listen_tcp = 1|listen_tcp = 1|' /etc/libvirt/libvirtd.conf
sudo sed -i 's|#auth_tcp = "sasl"|auth_tcp="none"|' /etc/libvirt/libvirtd.conf

# trusty
#sudo sed -i 's|env libvirtd_opts="-d"|env libvirtd_opts="-d -l"|' /etc/init/libvirt-bin.conf
#sudo sed -i 's|libvirtd_opts="-d"|libvirtd_opts="-d -l"|' /etc/default/libvirt-bin

# wily+
sudo sed -i 's|ExecStart=/usr/sbin/libvirtd \$libvirtd_opts|ExecStart=/usr/sbin/libvirtd -l \$libvirtd_opts|' /etc/systemd/system/multi-user.target.wants/libvirtd.service
sudo sed -i 's|ExecStart=/usr/sbin/libvirtd \$libvirtd_opts|ExecStart=/usr/sbin/libvirtd -l \$libvirtd_opts|' /lib/systemd/system/libvirtd.service

sudo systemctl daemon-reload
sudo service libvirt-bin restart

sudo usermod -a -G libvirt ubuntu
SCRIPT

$for_all = <<SCRIPT
sudo invoke-rc.d apparmor stop
sudo update-rc.d -f apparmor remove

sudo apt-get purge -qq -y --auto-remove chef puppet
sudo apt-get clean
sudo apt-get autoclean
SCRIPT

Vagrant.configure("2") do |config|

  # config.vm.box = "ubuntu/wily64"
  # config.vm.box = "ubuntu/xenial64"

  config.vm.box = "xenial64"
  config.vm.box_url = "http://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-vagrant.box"

  # config.vm.network "private_network", type: "dhcp"

  # config.vm.provider "libvirt" do |lv|
  #   lv.memory = "2048"
  # end

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end

  
  if Vagrant.has_plugin?("vagrant-hostmanager")
    config.hostmanager.enabled = true
    config.hostmanager.manage_guest = true
    config.hostmanager.manage_host = true
    config.hostmanager.ignore_private_ip = false
  end

  config.vm.synced_folder ".", "/vagrant", type: "nfs"
  config.vm.synced_folder "./shared_storage", "/var/lib/libvirt/images", type: "nfs"

  config.vm.define "node1" do |node|
    node.vm.network :private_network, ip: '192.168.42.11'
    config.vm.provider :virtualbox do |vb|
        vb.name = "xenial_node1"
        vb.memory = "3072"
    end
    node.vm.provision :shell, inline: <<-SHELL
      sudo hostnamectl set-hostname node1
    SHELL
    node.vm.provision :shell, inline: $main_script
  end

  config.vm.define "node2" do |node|
    node.vm.network :private_network, ip: '192.168.42.12'
    config.vm.provider :virtualbox do |vb|
        vb.name = "xenial_node2"
        vb.memory = "3072"
    end
    node.vm.provision :shell, inline: <<-SHELL
      sudo hostnamectl set-hostname node2
    SHELL
    node.vm.provision :shell, inline: $main_script
  end

  config.vm.define "node3" do |node|
    node.vm.network :private_network, ip: '192.168.42.13'
    config.vm.provider :virtualbox do |vb|
        vb.name = "xenial_node3"
    end
    
    config.vm.synced_folder "../orchestra", "/orchestra", type: "nfs"

    node.vm.provision :shell, inline: <<-SHELL
      sudo hostnamectl set-hostname node3

      echo "deb https://dl.bintray.com/sbt/debian /" | sudo tee -a /etc/apt/sources.list.d/sbt.list
      sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 642AC823
      sudo add-apt-repository ppa:webupd8team/java
      sudo apt-get update
      
      echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections

      sudo apt-get install -y oracle-java8-installer
      sudo apt-get install -y sbt ansible

      sudo apt-get purge -qq -y --auto-remove chef puppet
      sudo apt-get clean
      sudo apt-get autoclean
    SHELL
  end
  config.vm.provision :shell, inline: $for_all
end
