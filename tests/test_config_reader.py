from unittest import TestCase, main
import sys
from pyhocon import ConfigFactory
from gcdt.logger import setup_logger
from mock import Mock, MagicMock, patch

# Same response for all lockups
cloudformation_response = {
  "ClusterEndpointAddress": "redshift-test.dp.glomex.cloud",
  "ClusterEndpointPort": "5000",
  "RoleLambda": "arnApi",
  "SecurityGroup": "sg-ae6850ca"
}

class ConfigReaderTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment
        """
        # Load files to test
        sys.path.insert(1, '../dphelper')
        # Import file under test
        import config_reader
        # Make it accessible outside this method
        global config_reader

        # Build test logger
        log = setup_logger(logger_name="dphelper_configreader_test")

    def test_read(self):
        conf = config_reader.read_config("sample_settings", "resources", do_lookups=False)
        self.assertEquals(conf.get("redshift.stackName"), "dp-dev-store-redshift")

    @patch('config_reader.servicediscovery.get_outputs_for_stack',return_value=cloudformation_response)
    def test_lookup(self, get_outputs_for_stack_function):

        conf = config_reader.read_config("sample_settings", "resources", do_lookups=True)

        self.assertEquals(conf.get("redshift.clusterEndpointPort"), "5000")           # Lookup

        self.assertEquals(conf.get("lambdas.entries")[0].get("role"), "arnApi")       # Lookup in complex array

        self.assertEquals(conf.get("lambdas.vpc.subnetIds")[0], "subnet-87685dde")    # Keep in array

        self.assertEquals(conf.get("lambdas.vpc.securityGroups")[0], "sg-ae6850ca")   # Lookup in array

        self.assertEquals(conf.get("lambdas.timeout"), 300)                           # Keep int

if __name__ == "__main__":
    main()
