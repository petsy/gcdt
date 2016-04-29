from unittest import TestCase, main
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../gcdt")
import monitoring
import inspect


@monitoring.send_to_slacker("systemmessages", "testing...")
def test_decorator():
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    print 'function name "%s"' % inspect.getframeinfo(frame)[2]
    for i in args:
        print "    %s = %s" % (i, values[i])
    return [(i, values[i]) for i in args]


class MonitoringTestCase(TestCase):

    def test_send_to_slacker(self):
       # test_decorator("test_string")
       # don't use decorator right now
       # need to figure out a version that works for methods and functions
       pass

if __name__ == "__main__":
    # unittest.main()
    main()
