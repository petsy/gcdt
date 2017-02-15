# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
from unittest import TestCase
import mock

from gcdt import config_reader
from gcdt.config_reader import ConfigFactory


class TestConfigReader(TestCase):
    @classmethod
    def setUpClass(cls):
        """Prepare environment
        """
        cls.env = os.environ.get('ENV', None)
        # Set environment
        os.environ['ENV'] = 'LOCAL'

    @classmethod
    def tearDownClass(cls):
        """Fix environment after test"""
        # undo sideeffects of config_reader tests to limit neg. impact on others
        if cls.env:
            os.environ['ENV'] = cls.env

    def setUp(self):
        print('UNIT-TEST run: {}'.format(self._testMethodName))

    def test_get_env(self):
        os.environ['ENV'] = 'LOCAL'
        env = config_reader.get_env()
        self.assertEqual(env, config_reader.ENV_LOCAL)

        os.environ['ENV'] = 'NONE_SENSE'
        env = config_reader.get_env()
        self.assertEqual(env, None)

    def test_get_config_name(self):
        name = config_reader.get_config_name('test')
        self.assertEqual(name, 'test_local.conf')

        os.environ['ENV'] = 'qa'
        name = config_reader.get_config_name('test')
        self.assertEqual(name, 'test_qa.conf')

        name = config_reader.get_config_name('test', add_env=False)
        self.assertEqual(name, 'test.conf')

    @mock.patch('gcdt.config_reader.ConfigFactory.parse_file')
    def test_read_config_simple(self, mock_parse_file):
        # Mock Input (Config)
        mock_parse_file.return_value = ConfigFactory.parse_string(
            """{
                string = "TEST_STRING"
                integer = 10
                boolean = True
            }"""
        )

        conf = config_reader.read_config('NO_FILE_JUST_MOCK')

        self.assertEqual(conf.get('string'), 'TEST_STRING')
        self.assertEqual(conf.get('integer'), 10)
        self.assertEqual(conf.get('boolean'), True)

    @mock.patch('gcdt.config_reader.ConfigFactory.parse_file')
    def test_read_config_simple_level(self, mock_parse_file):
        # Mock Input (Config)
        mock_parse_file.return_value = ConfigFactory.parse_string(
            """level {
                string = "TEST_STRING"
                boolean = False
            }"""
        )

        conf = config_reader.read_config('NO_FILE_JUST_MOCK')

        self.assertEqual(conf.get('level.string'), 'TEST_STRING')
        self.assertEqual(conf.get('level.boolean'), False)

    @mock.patch('gcdt.config_reader.ConfigFactory.parse_file')
    @mock.patch('gcdt.config_reader.get_outputs_for_stack')
    def test_read_config_mock_service_discovery_stack(
            self, mock_get_outputs_for_stack, mock_parse_file):
        # Mock Output (Desc Stack)
        mock_get_outputs_for_stack.return_value = {
            'EC2BasicsLambdaArn':
                'arn:aws:lambda:eu-west-1:1122233:function:dp-preprod-lambdaEC2Basics-12',
        }
        # Mock Input (Config)
        mock_parse_file.return_value = ConfigFactory.parse_string(
            """{
                string = "lookup:stack:dp-preprod:EC2BasicsLambdaArn"
            }"""
        )

        conf = config_reader.read_config('NO_FILE_JUST_MOCK')
        self.assertEqual(conf.get('string'), 'arn:aws:lambda:eu-west-1:1122233:function:dp-preprod-lambdaEC2Basics-12')

    @mock.patch('gcdt.config_reader.ConfigFactory.parse_file')
    @mock.patch('gcdt.config_reader.get_ssl_certificate')
    def test_read_config_mock_service_discovery_ssl(
            self, mock_get_ssl_certificate, mock_parse_file):
        # Mock Output (List SSL Certs)
        mock_get_ssl_certificate.return_value = 'arn:aws:iam::11:server-certificate/cloudfront/2016/wildcard.dp.glomex.cloud-2016-03'
        # Mock Input (Config)
        mock_parse_file.return_value = ConfigFactory.parse_string(
            """{
                string = "lookup:ssl:wildcard.dp.glomex.cloud-2016-03"
            }"""
        )

        conf = config_reader.read_config('NO_FILE_JUST_MOCK')
        self.assertEqual(conf.get('string'),
                         'arn:aws:iam::11:server-certificate/cloudfront/2016/wildcard.dp.glomex.cloud-2016-03')

    @mock.patch('gcdt.config_reader.ConfigFactory.parse_file')
    @mock.patch('gcdt.config_reader.get_secret')
    def test_read_config_mock_service_discovery_secret(self, mock_get_secret,
                                                       mock_parse_file):
        # Mock Output (Credstash result)
        mock_get_secret.return_value = 'secretPassword'
        # Mock Input (Config)
        mock_parse_file.return_value = ConfigFactory.parse_string(
            """{
                string = "lookup:secret:nameOfSecretPassword"
            }"""
        )

        conf = config_reader.read_config('NO_FILE_JUST_MOCK')
        self.assertEqual(conf.get('string'), 'secretPassword')

    @mock.patch('gcdt.config_reader.ConfigFactory.parse_file')
    @mock.patch('gcdt.config_reader.get_ssl_certificate')
    @mock.patch('gcdt.config_reader.get_secret')
    @mock.patch('gcdt.config_reader.get_outputs_for_stack')
    def test_read_config_mock_selective_stack_lookup(
            self, mock_get_outputs_for_stack, mock_get_secret, \
            mock_get_ssl_certificate, mock_parse_file):
        # Mock Output (Credstash result)
        mock_get_secret.return_value = 'secretPassword'
        # Mock Output (SSL Cert)
        mock_get_ssl_certificate.return_value = 'arn:aws:iam::11:server-certificate/cloudfront/2016/wildcard.dp.glomex.cloud-2016-03'
        # Mock Output (Desc Stack)
        mock_get_outputs_for_stack.return_value = {
            'EC2BasicsLambdaArn': 'arn:aws:lambda:eu-west-1:1122233:function:dp-preprod-lambdaEC2Basics-12',
        }

        # Mock Input (Config)
        mock_parse_file.return_value = ConfigFactory.parse_string(
            """{
                secret = "lookup:secret:nameOfSecretPassword"
                sslCert = "lookup:ssl:wildcard.dp.glomex.cloud-2016-03"
                stack = "lookup:stack:dp-preprod:EC2BasicsLambdaArn"
            }"""
        )

        conf = config_reader.read_config('NO_FILE_JUST_MOCK')
        self.assertEqual(conf.get('secret'), 'secretPassword')
        self.assertEquals(conf.get('sslCert'), 'arn:aws:iam::11:server-certificate/cloudfront/2016/wildcard.dp.glomex.cloud-2016-03')
        self.assertEqual(conf.get('stack'), 'arn:aws:lambda:eu-west-1:1122233:function:dp-preprod-lambdaEC2Basics-12')
        conf_only_stack_lookup = config_reader.read_config('NO_FILE_JUST_MOCK',
                                                           lookups=['stack'])
        self.assertEqual(conf_only_stack_lookup.get('secret'), 'lookup:secret:nameOfSecretPassword')
        self.assertEquals(conf_only_stack_lookup.get('sslCert'), 'lookup:ssl:wildcard.dp.glomex.cloud-2016-03')
        self.assertEqual(conf_only_stack_lookup.get('stack'), 'arn:aws:lambda:eu-west-1:1122233:function:dp-preprod-lambdaEC2Basics-12')

        conf_only_secret_lookup = config_reader.read_config('NO_FILE_JUST_MOCK',
                                                            lookups=['secret'])
        self.assertEqual(conf_only_secret_lookup.get('secret'), 'secretPassword')
        self.assertEquals(conf_only_secret_lookup.get('sslCert'), 'lookup:ssl:wildcard.dp.glomex.cloud-2016-03')
        self.assertEqual(conf_only_secret_lookup.get('stack'), 'lookup:stack:dp-preprod:EC2BasicsLambdaArn')

        conf_only_ssl_lookup = config_reader.read_config('NO_FILE_JUST_MOCK',
                                                         lookups=['ssl'])
        self.assertEqual(conf_only_ssl_lookup.get('secret'), 'lookup:secret:nameOfSecretPassword')
        self.assertEquals(conf_only_ssl_lookup.get('sslCert'), 'arn:aws:iam::11:server-certificate/cloudfront/2016/wildcard.dp.glomex.cloud-2016-03')
        self.assertEqual(conf_only_ssl_lookup.get('stack'), 'lookup:stack:dp-preprod:EC2BasicsLambdaArn')
