#!/bin/bash -e

# Build python package and upload to PyPi

# build the package and publish to repo server
./venv/bin/python setup.py sdist --dist-dir dist/

# publish the package to repo server
./venv/bin/aws s3 cp --acl bucket-owner-full-control ./dist/ s3://$BUCKET --recursive --exclude '*' --include '*.tar.gz'

# wait for package to be available on PyPi server
# sync is implemented via crontab => 60 seconds
sleep 90
