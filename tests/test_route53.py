# -*- coding: utf-8 -*-

from nose.tools import (
    assert_true,
    assert_equal,
)

from gcdt import route53

from troposphere.ec2 import Instance


def test_create_record_with_given_hostname():
    result_record = route53.create_record(
        "TESTPREFIX",
        "120.0.0.1",
        host_zone_name="TEST.HOST.ZONE.",
    )

    # Compare HostedZoneName
    assert_equal(result_record.HostedZoneName, "TEST.HOST.ZONE.")
    # Compare Name : DNS name used as URL later on
    assert_equal(result_record.Name.data, {'Fn::Join': ['', ['TESTPREFIX.', 'TEST.HOST.ZONE.']]})
    # Compare ResourceRecords : The target for the route
    assert_equal(result_record.ResourceRecords, ["120.0.0.1"])
    # Compare Type : The default should be "A"
    assert_equal(result_record.Type, "A")
    # Compare TTL
    assert_equal(result_record.TTL, route53.TTL_DEFAULT)


def test_create_record_with_given_hostname_cname():
    result_record = route53.create_record(
        "TESTPREFIX",
        "120.0.0.1",
        host_zone_name="TEST.HOST.ZONE.",
        type="CNAME"
    )

    # Compare HostedZoneName
    assert_equal(result_record.HostedZoneName, "TEST.HOST.ZONE.")
    # Compare Name : DNS name used as URL later on
    assert_equal(result_record.Name.data, {'Fn::Join': ['', ['TESTPREFIX.', 'TEST.HOST.ZONE.']]})
    # Compare ResourceRecords : The target for the route
    assert_equal(result_record.ResourceRecords, ["120.0.0.1"])
    # Compare Type
    assert_equal(result_record.Type, "CNAME")
    # Compare TTL
    assert_equal(result_record.TTL, route53.TTL_DEFAULT)


def test_create_record_with_given_hostname_target_instance():
    instance = Instance("testEC2")

    result_record = route53.create_record(
        "TESTPREFIX",
        instance,
        host_zone_name="TEST.HOST.ZONE.",
    )

    # Compare HostedZoneName
    assert_equal(result_record.HostedZoneName, "TEST.HOST.ZONE.")
    # Compare Name : DNS name used as URL later on
    assert_equal(result_record.Name.data, {'Fn::Join': ['', ['TESTPREFIX.', 'TEST.HOST.ZONE.']]})
    # Compare ResourceRecords : The target for the route
    assert_equal(result_record.ResourceRecords[0].data, {'Fn::GetAtt': ['testEC2', 'PrivateIp']})
    # Compare Type
    assert_equal(result_record.Type, "A")
    # Compare TTL
    assert_equal(result_record.TTL, route53.TTL_DEFAULT)
