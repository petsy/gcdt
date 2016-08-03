from __future__ import print_function
import sys
from time import sleep


__version__ = '0.0.29'


def version(out=sys.stdout):
    """Print version of gcdt tools."""
    print("gcdt version %s" % __version__, file=out)


def get_git_revision_short_hash():
    # TODO: is this a good idea? (how to make sure that git is installed)?
    from string import strip
    import subprocess
    return strip(subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']))


'''looks like this is no longer used...
def example_exc_handler(tries_remaining, exception, delay):
    """Example exception handler; prints a warning to stderr.

    tries_remaining: The number of tries remaining.
    exception: The exception instance which was raised.
    """
    print >> sys.stderr, "Caught '%s', %d tries remaining, sleeping for %s seconds" % (exception, tries_remaining, delay)
'''


def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
    """Function decorator implementing retrying logic.

    delay: Sleep this many seconds * backoff * try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature myhook(tries_remaining, exception);
          default None

    The decorator will call the function up to max_tries times if it raises
    an exception.

    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.

    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """
    def dec(func):
        def f2(*args, **kwargs):
            mydelay = delay
            tries = range(max_tries)
            tries.reverse()
            for tries_remaining in tries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)
                        sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    break
        return f2
    return dec
