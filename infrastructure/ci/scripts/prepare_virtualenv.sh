#!/bin/bash -e

# prepare virtualenv

# initialize
virtualenv --clear venv
virtualenv -p /usr/bin/python2.7 --no-site-packages venv

# create pip.conf file
echo "[global]
timeout = 20
extra-index-url = https://reposerver-prod-eu-west-1.infra.glomex.cloud/pypi/packages
trusted-host = reposerver-prod-eu-west-1.infra.glomex.cloud" >> ./venv/pip.conf

# install gcdt development tools
./venv/bin/pip install -r requirements_dev.txt

# compile and install requirements
rm requirements.txt
./venv/bin/pip-compile requirements.in
./venv/bin/pip install -r requirements.txt -r requirements_dev.txt

# install gcdt development version
./venv/bin/pip install -e .
