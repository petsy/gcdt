from unittest import TestCase, main
import sys
sys.path.append("../gcdt/")

from servicediscovery import get_ssl_certificate

class MonitoringTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_ssl_certificate(self):
        existing_stack = "dp-dev"
        print get_ssl_certificate("wildcard.glomex.com")
        #self.assertTrue(stack_exists(existing_stack))
        #self.assertFalse(stack_exists(non_existing_stack))




if __name__ == "__main__":
    main()