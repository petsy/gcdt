import sys
from os import path, environ
environ['ENV']='LOCAL'
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) + "/gcdt/")

from unittest import TestCase
from nose.plugins.attrib import attr
from pyhocon import ConfigFactory

from kumo_tool import stack_exists, create_change_set, generate_parameters

@attr("unit")
class KumoUnitTestCase(TestCase):

    def test_config_reading(self):
        config_string = """
        cloudformation {
            ConfigOne = value1
            ConfigTwo = [value2, value3]
        }
        """
        expected = [
            {
                "ParameterKey": "ConfigOne",
                "ParameterValue": "value1",
                "UsePreviousValue": False
            },
            {
                "ParameterKey": "ConfigTwo",
                "ParameterValue": "value2,value3",
                "UsePreviousValue": False
            }
        ]
        conf = ConfigFactory.parse_string(config_string)
        converted_conf = generate_parameters(conf)
        self.assertEqual(converted_conf, expected)
