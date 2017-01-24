#!/bin/sh
set -e

VENV_GCDT=~/.venv-gcdt
REPO_SERVER="https://reposerver-prod-eu-west-1.infra.glomex.cloud/pypi/packages"

#### check python version
VERSION="$(python -c 'import platform; print(platform.python_version())')"
if  [[ $VERSION != 2.7.9 ]] && [[ $VERSION != 2.7.1* ]] ;
then
    echo "You have Python $VERSION installed."
    echo "Please install python version 2.7.9 or preferably higher."
    exit 1
fi


## check for VPN connection
if curl --output /dev/null --silent --head --connect-timeout 10 --fail "$REPO_SERVER"
then
    echo "VPN ok"
else
    echo "No VPN connection. Please use FortiClient to connect to VPN."
    exit 1
fi

#### make sure we can use bash
brew install bash


#### make sure we have virtualenv
#TODO
#pip install virtualenv

echo "gcdt installation..."


#### prepare .venv-gcdt
virtualenv $VENV_GCDT
cat <<EOF >$VENV_GCDT/pip.conf
[global]
timeout = 20
extra-index-url = https://reposerver-prod-eu-west-1.infra.glomex.cloud/pypi/packages
trusted-host = reposerver-prod-eu-west-1.infra.glomex.cloud
EOF


#### install gcdt
$VENV_GCDT/bin/pip install gcdt


#### write the extension to .bash_profile
cat <<EOF >~/.gcdtrc
# this script has been installed by the glomex-cloud-deployment-tools installer (gcdt)
# it has been tested on OS X El Capitan (10.11.6)


VENV_GCDT=~/.venv-gcdt

check_venv() {
    # check if we run in user defined virutalenv; if not then setup or activate virtualenv for gcdt
    if [ ! -z "\$VIRTUAL_ENV" ]
    then
        # already running in virtualenv (do nothing)
        # echo \$VIRTUAL_ENV
        IN_USR_VENV=true
    else
        # not running in a virtualenv; activate virtualenv for gcdt
        if [ ! -d \$VENV_GCDT ] ; then echo "You gcdt installation appears to be broken. Please reinstall gcdt!"; return; fi
        source \$VENV_GCDT/bin/activate
        IN_USR_VENV=false
    fi
}

gcdt() {
    check_venv;
    python -m gcdt.gcdt_main \$@
    if [ "\$IN_USR_VENV" = false ] ; then deactivate; fi
}

kumo() {
    check_venv;
    python -m gcdt.kumo_main \$@
    if [ "\$IN_USR_VENV" = false ] ; then deactivate; fi
}

tenkai() {
    check_venv;
    python -m gcdt.tenkai_main \$@
    if [ "\$IN_USR_VENV" = false ] ; then deactivate; fi
}

ramuda() {
    check_venv;
    python -m gcdt.ramuda_main \$@
    if [ "\$IN_USR_VENV" = false ] ; then deactivate; fi
}

yugen() {
    check_venv;
    python -m gcdt.yugen_main \$@
    if [ "\$IN_USR_VENV" = false ] ; then deactivate; fi
}
EOF

#### add source statement to .bash_profile
grep -q '^source .gcdtrc' ~/.bash_profile || echo 'source .gcdtrc' >> ~/.bash_profile


#### run gcdt version
source ~/.gcdtrc
echo "gcdt installation complete..."
gcdt version

echo
echo "Please restart your terminal before using gcdt."
echo "Talk to you soon. Your glomex OPS team."
