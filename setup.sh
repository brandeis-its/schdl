#!/bin/bash

if grep -qir 'red.?hat' /etc/issue then
    DISTRO=redhat
elif grep -qir 'ubuntu' /etc/issue then
    DISTRO=ubuntu
elif grep -qir 'debian' /etc/issue then
    DISTRO=debian
else 
    echo 'Failed to detect Red Hat, Debian, or Ubuntu' >&2
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
    sudo sh -c 'wget -qO- http://people.redhat.com/bkabrda/scl_python27.repo >> /etc/yum.repos.d/scl.repo'
    sudo yum install python27
    . /opt/rh/python27/enable
    sudo yum -y install nodejs mongodb-org-server mongodb-org python-virtualenv
    sudo yum -y groupinstall 'Development Tools'
    sudo semanage port -a -t mongod_port_t -p tcp 27017
    sudo service mongod start
else
    sudo ${INSTALL_CMD} build-essential npm mongodb
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
