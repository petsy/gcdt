#!/bin/bash -e


# build the package and publish to repo server
./venv/bin/python setup.py sdist --dist-dir dist/

# publish the package to repo server
aws s3 cp --acl bucket-owner-full-control ./dist/ s3://$BUCKET --recursive --exclude '*' --include '*.tar.gz'

# wait for package to be available on PyPi server
# checked with Michael Ludwig, the sync interval is 30 sec
# obviously this was misplaced
sleep 330
