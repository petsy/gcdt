#!/bin/bash -e
#
# Dependency compile & version bumping (dev level) on develop branch

########
# Preparation

# Setup virtualenv in temp folder
TEMP_DIR=`mktemp -d` && cd ${TEMP_DIR}
virtualenv -p /usr/bin/python2.7 --no-site-packages venv

# create pip.conf file
echo "[global]
timeout = 20
extra-index-url = https://reposerver-prod-eu-west-1.infra.glomex.cloud/pypi/packages
trusted-host = reposerver-prod-eu-west-1.infra.glomex.cloud" >> ./venv/pip.conf

source ./venv/bin/activate


########
# Debug
echo "-INPUT---------------"
echo "AWS_DEFAULT_REGION   : ${AWS_DEFAULT_REGION}"
echo "BRANCH          	   : ${PYPI_REPO}"
echo "WORKSPACE            : ${WORKSPACE}"
echo "TEMP_DIR             : ${TEMP_DIR}"
echo "ENV                  : ${ENV}"
echo "PACKAGE_NAME         : ${PACKAGE_NAME}"
echo "ARTIFACT_BUCKET      : ${ARTIFACT_BUCKET}"
echo "PYTHONUNBUFFERED     : ${PYTHONUNBUFFERED}"
echo "BUCKET               : ${BUCKET}"
echo "-INPUT END-----------"


########
# Dependency Compile
cd $WORKSPACE
pip install -r requirements_dev.txt

#rm -f requirements.txt
#pip-compile requirements.in
pip install -r requirements.txt -r requirements_dev.txt

#Check if we need to commit changes to requirements.txt
#IS_DIRTY=$(git diff-index --quiet HEAD --; echo $?)
#echo $IS_DIRTY
#git diff

#if [ $IS_DIRTY -eq 1 ]
#then
#  echo "commiting changes to requirments.txt" && git commit -v -a -m "recompiled requirements" || echo "0"
#fi

########
# Version
echo "bumping dev level in develop"
bumpversion --commit dev


########
# Release
python setup.py sdist --dist-dir dist/
ls -la dist/

# install the awscli
#pip install awscli --ignore-installed six

# publish to repo server
aws s3 cp --acl bucket-owner-full-control ./dist/ s3://$BUCKET --recursive --exclude '*' --include '*.tar.gz'


########
#clean up
rm -rf ${TEMP_DIR}
