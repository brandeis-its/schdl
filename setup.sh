#!/bin/bash

if egrep -qi 'red.?hat' /etc/issue; then
    # Tested with RHEL 6
    DISTRO=redhat
elif grep -qi 'ubuntu' /etc/issue; then
    # Tested with Ubuntu 18.04
    DISTRO=ubuntu
else 
    echo 'Failed to detect Red Hat or Ubuntu' >&2
    exit 1
fi

if [[ ${DISTRO} == redhat ]]; then
    curl --silent --location https://rpm.nodesource.com/setup_10.x | sudo bash -
    sudo tee '/etc/yum.repos.d/mongodb-org-4.0.repo' > /dev/null <<'EOF'
[mongodb-org-4.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.0.asc
EOF
    # RHEL 6 doesn't have python2.7
    if [[ ! -e /opt/rh/python27/enable ]]; then
        sudo sh -c 'wget -qO- http://people.redhat.com/bkabrda/scl_python27.repo >> /etc/yum.repos.d/scl.repo'
        sudo yum install python27
    fi
    . /opt/rh/python27/enable
    sudo yum -y install nodejs mongodb-org-server mongodb-org python-virtualenv
    sudo yum -y groupinstall 'Development Tools'
    sudo semanage port -a -t mongod_port_t -p tcp 27017
    sudo service mongod start
else
    sudo apt-get --assume-yes install build-essential npm mongodb python-virtualenv python-dev
    sudo service mongodb start
fi

. schdl.env
virtualenv venv
. venv/bin/activate

pip install -r requirements.txt
nodeenv -p -n system
deactivate
. venv/bin/activate
cd ui
npm install
npm install -g grunt-cli bower
bower install
cd ..
mkdir ~/schdl-bin
./build.sh ~/schdl-bin

# bin/addSchool.py ...
# bin/ensureIndices.py
