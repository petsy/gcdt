#!/usr/bin/env bash
#
# Script reacts to CodeDeploy lifecycle events and installs application
# http://docs.aws.amazon.com/codedeploy/latest/userguide/app-spec-ref-hooks.html

# Parameters
DESTINATION_PATH="/etc/ansible/codedeploy"

if [ "$LIFECYCLE_EVENT" == "ApplicationStop" ] ; then
    echo "LIFECYCLE_EVENT=ApplicationStop"

elif [ "$LIFECYCLE_EVENT" == "BeforeInstall" ] ; then
    echo "LIFECYCLE_EVENT=BeforeInstall"

elif [ "$LIFECYCLE_EVENT" == "AfterInstall" ] ; then
    echo "LIFECYCLE_EVENT=AfterInstall"

elif [ "$LIFECYCLE_EVENT" == "ApplicationStart" ] ; then
    echo "LIFECYCLE_EVENT=ApplicationStart"

elif [ "$LIFECYCLE_EVENT" == "ValidateService" ] ; then
    echo "LIFECYCLE_EVENT=ApplicationStart"
fi
