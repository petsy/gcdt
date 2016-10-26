#!/bin/bash -e
#
# Tool to build python packages and deploy them to our PyPi

########
# Config

export AWS_DEFAULT_REGION=eu-west-1

case $BRANCH in
  master)
        export ENV=prod
        ;;
esac

# Setup virtualenv
TEMP_DIR=`mktemp -d` && cd ${TEMP_DIR}
virtualenv -p /usr/bin/python2.7 venv --no-site-packages
source venv/bin/activate

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
echo "-INPUT END-----------"

########
# Dependency Compile

cd $WORKSPACE

# pinning to 8.1.1 for pip-tools compatibility
pip install --upgrade pip==8.1.1
pip install pep8
pip install pylint
pip install nose
pip install bumpversion
pip install pip-tools

rm requirements.txt
pip-compile requirements.in
pip install -r requirements.txt

#Check if we need to commit changes to requirements.txt
IS_DIRTY=$(git diff-index --quiet HEAD --; echo $?)
echo $IS_DIRTY
git diff

if [ $IS_DIRTY -eq 1 ]
then
  echo "commiting changes to requirments.txt" && git commit -v -a -m "recompiled requirements" || echo "0"
fi

########
# Test

docker build -t $PACKAGE_NAME .

########
# Version

case $ENV in
  preprod)
      echo "bumping dev level in develop"
      bumpversion --commit dev
      ########
      # Do

      # build
      #cd ..
      python setup.py sdist --dist-dir dist/
      ls -la dist/

      # publish to repo server
      BUCKET=$ARTIFACT_BUCKET/pypi/packages/$PACKAGE_NAME/
      aws s3 cp --acl bucket-owner-full-control ./dist/ s3://$BUCKET --recursive --exclude '*' --include '*.tar.gz'
      ;;
  prod)
      git checkout master
      echo "bumping version to release"
      bumpversion --commit --tag release
      git checkout develop
      git merge master
      ########
      # Do

      # build
      #cd ..
      python setup.py sdist --dist-dir dist/
      ls -la dist/

      # publish to repo server
      BUCKET=$ARTIFACT_BUCKET/pypi/packages/$PACKAGE_NAME/
      aws s3 cp --acl bucket-owner-full-control ./dist/ s3://$BUCKET --recursive --exclude '*' --include '*.tar.gz'

      # now we need to bump patch level
      echo "bumping patch level"
      bumpversion --commit patch
      ;;
  esac

#clean up
rm -rf ${TEMP_DIR}
