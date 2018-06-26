#!/bin/bash

. schdl.env
virtualenv venv
. venv/bin/activate
sudo apt-get install build-essential npm mongodb
sudo service mongodb start
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
