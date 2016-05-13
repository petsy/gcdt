from unittest import TestCase, main
import sys
from pyhocon import ConfigFactory

sys.path.append("../gcdt/")

from config_reader import resolve_lookups

class MonitoringTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_resolve_lookups(self):
        config_string = """lambda {
            applicationName = "lookup:dp-dev-operations-jenkins-jobr:ApplicationName",
            sslcert = "ssl:wildcard.glomex.com"
                            }"""
        conf = ConfigFactory.parse_string(config_string)
        print resolve_lookups(conf)


if __name__ == "__main__":
    main()