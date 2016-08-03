import boto3
import os
from StringIO import StringIO
from nose.plugins.skip import SkipTest
from nose.tools import assert_equal, assert_false, \
    assert_regexp_matches, with_setup
import nose
from nose.tools import assert_is_not
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree
from gcdt.kumo_core import load_cloudformation_template, list_stacks, \
    print_parameter_diff, are_credentials_still_valid, deploy_stack, \
    delete_stack, create_change_set, _get_stack_name, describe_change_set


def here(p): return os.path.join(os.path.dirname(__file__), p)

# slack_token for testing (the one Jenkins uses):
slack_token = '***REMOVED***'

boto_session = boto3.session.Session()

# read template and config
cloudformation, _ = load_cloudformation_template(
    here('resources/simple_cloudformation_stack/cloudformation.py')
)
config = ConfigFactory.parse_file(
    here('resources/simple_cloudformation_stack/settings_dev.conf')
)


def check_preconditions():
    """Make sure the default profile is set"""
    if not os.getenv('AWS_DEFAULT_PROFILE', None):
        # http://stackoverflow.com/questions/1120148/disabling-python-nosetests/1843106
        print("AWS_DEFAULT_PROFILE variable not set! Test is skipped.")
        raise SkipTest("AWS_DEFAULT_PROFILE variable not set! Test is skipped.")
    # export AWS_DEFAULT_PROFILE=superuser-qa-dev => README.md
    if not os.getenv('ENV', None):
        print("ENV environment variable not set! Test is skipped.")
        raise SkipTest("ENV environment variable not set! Test is skipped.")


@with_setup(check_preconditions)
def test_list_stacks():
    out = StringIO()
    list_stacks(boto_session, out=out)
    assert_regexp_matches(out.getvalue().strip(), 'listed \d+ stacks')


@with_setup(check_preconditions)
def test_print_parameter_diff():
    out = StringIO()
    empty_conf = ConfigTree([('cloudfoundation', ConfigTree([]))])

    print_parameter_diff(boto_session, empty_conf, out=out)
    assert_regexp_matches(out.getvalue().strip(),
        'StackName is not configured, could not create parameter diff')


# most kumo-operations which rely on a stack on AWS can not be tested in isolation
# since the stack creation for a simple stack takes some time we decided
# to test the stack related operations together

def cleanup_stack():
    """Remove the stack to cleanup after test run.

    This is intended to be called during test teardown"""
    exit_code = delete_stack(boto_session, config, slack_token)
    # check whether delete was completed!
    assert_false(exit_code, 'delete_stack was not completed\n' +
                 'please make sure to clean up the stack manually')


@with_setup(check_preconditions, cleanup_stack)
def test_kumo_stack_lifecycle():
    # create a stack we use for the test lifecycle
    print_parameter_diff(boto_session, config)
    are_credentials_still_valid(boto_session)
    exit_code = deploy_stack(boto_session, config, cloudformation,
                             slack_token, override_stack_policy=False)
    assert_equal(exit_code, 0)

    ## preview (with identical stack)
    # TODO: add more asserts!
    change_set_name, stackname = \
        create_change_set(boto_session, config, cloudformation)
    assert_equal(stackname, _get_stack_name(config))
    assert_is_not(change_set_name, '')
    describe_change_set(boto_session, change_set_name, stackname)

    ## update the stack
    print_parameter_diff(boto_session, config)
    exit_code = deploy_stack(boto_session, config, cloudformation,
                             slack_token, override_stack_policy=False)
    assert_equal(exit_code, 0)
