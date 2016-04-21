from unittest import TestCase, main
import sys
sys.path.append("../gcdt/")

from kumo_tool import stack_exists, create_change_set

class MonitoringTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        # shutil.rmtree(os.getcwdu()+"/resources/vendored")
        pass

    def test_stack_exists(self):
        existing_stack = "dp-dev"
        non_existing_stack = "fonsi"
        self.assertTrue(stack_exists(existing_stack))
        self.assertFalse(stack_exists(non_existing_stack))

    def test_create_change_set(self):
        pass


if __name__ == "__main__":
    # unittest.main()
    main()
