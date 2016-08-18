# -*- coding: utf-8 -*-
from nose.tools import assert_dict_equal
from nose.tools import assert_equal, assert_true, \
    assert_regexp_matches, assert_list_equal, raises
import nose
import os
import shutil
import json
from tempfile import NamedTemporaryFile, mkdtemp
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree
from gcdt import kumo_core
from gcdt.kumo_core import configure, read_kumo_config, _generate_parameters, \
    load_cloudformation_template, generate_template_file, _get_stack_name, \
    _get_stack_policy, _get_stack_policy_during_update, _get_conf_value, \
    _generate_parameter_entry
from pyhocon.exceptions import ConfigMissingException


def here(p): return os.path.join(os.path.dirname(__file__), p)


def test_configure():
    stackname = 'my_stack'

    def fake_get_input():
        return stackname

    kumo_core._get_input = fake_get_input

    tf = NamedTemporaryFile(delete=False)
    configure(tf.name)
    assert_equal(open(tf.name).read(), 'kumo {\nslack-token=%s\n}' % stackname)

    # cleanup the testfile
    tf.close()
    os.unlink(tf.name)


def test_read_kumo_config():
    stackname = 'my_stack'

    tf = NamedTemporaryFile(delete=False)
    open(tf.name, 'w').write('kumo {\nslack-token=%s\n}' % stackname)

    expected = ConfigTree([('kumo', ConfigTree([('slack-token', stackname)]))])
    actual, exit_code = read_kumo_config(tf.name)
    assert_equal(exit_code, 0)
    assert_equal(actual, expected)

    # cleanup the testfile
    tf.close()
    os.unlink(tf.name)


def test_parameter_substitution():
    config_string = '''
    cloudformation {
        ConfigOne = value1
        ConfigTwo = [value2, value3]
    }
    '''
    expected = [
        {
            'ParameterKey': 'ConfigOne',
            'ParameterValue': 'value1',
            'UsePreviousValue': False
        },
        {
            'ParameterKey': 'ConfigTwo',
            'ParameterValue': 'value2,value3',
            'UsePreviousValue': False
        }
    ]
    conf = ConfigFactory.parse_string(config_string)
    converted_conf = _generate_parameters(conf)
    assert_equal(converted_conf, expected)


def test_load_cloudformation_template():
    tf = NamedTemporaryFile(delete=False, suffix='py')
    open(tf.name, 'w').write('def plus(a, b):\n    return a+b')

    module, success = load_cloudformation_template(tf.name)
    assert_equal(success, True)
    assert_equal(module.plus(1, 2), 3)

    # cleanup the testfile
    tf.close()
    os.unlink(tf.name)


def test_cloudformation_template_not_available():
    module, success = load_cloudformation_template()
    assert_equal(module, None)
    assert_equal(success, False)


def test_load_cloudformation_template_from_cwd():
    cwd = (os.getcwd())
    # prepare dummy template for test
    folder = mkdtemp()
    os.chdir(folder)
    open('cloudformation.py', 'w').write('def plus(a, b):\n    return a+b\n')

    module, success = load_cloudformation_template()
    assert_true(success, True)
    assert_equal(module.plus(1, 2), 3)

    # cleanup
    os.chdir(cwd)
    shutil.rmtree(folder)


def test_simple_cloudformation_stack():
    # read the template
    template_path = here(
        'resources/simple_cloudformation_stack/cloudformation.py')
    config_path = here(
        'resources/simple_cloudformation_stack/settings_dev.conf')

    cloudformation, success = load_cloudformation_template(template_path)
    assert_true(success)
    # read the configuration
    config = ConfigFactory.parse_file(config_path)

    expected_templ_file_name = '%s-generated-cf-template.json' % _get_stack_name(
        config)
    actual = generate_template_file(config, cloudformation)
    assert_equal(actual, expected_templ_file_name)


def _create_simple_cf():
    # http://code.activestate.com/recipes/52308-the-simple-but-handy-collector-of-a-bunch-of-named/?in=user-97991
    class Bunch:
        def __init__(self, **kwds):
            self.__dict__.update(kwds)

    # use Bunch to create group of variables:
    # cf = Bunch(datum=y, squared=y*y, coord=x)
    cf = Bunch()
    return cf


def test_simple_cloudformation_stack_default():
    cf = _create_simple_cf()
    stack_policy = _get_stack_policy(cf)
    # policy defined in _get_stack_policy is used
    assert_regexp_matches(stack_policy, '{"Statement":')


def test_simple_cloudformation_stack_custom():
    def gsp():
        return 'have indiv. policy'
    cf = _create_simple_cf()
    cf.get_stack_policy = gsp
    stack_policy = _get_stack_policy(cf)
    assert_equal(stack_policy, 'have indiv. policy')


def test_simple_cloudformation_stack_during_update_custom():
    def gsp():
        return 'have indiv. policy'
    cf = _create_simple_cf()
    cf.get_stack_policy_during_update = gsp
    stack_policy = _get_stack_policy_during_update(cf, False)
    assert_equal(stack_policy, 'have indiv. policy')


def test_simple_cloudformation_stack_during_update_override_custom():
    # test make sure override has no impact on custom policy
    def gsp():
        return 'have indiv. policy'
    cf = _create_simple_cf()
    cf.get_stack_policy_during_update = gsp
    stack_policy = _get_stack_policy_during_update(cf, True)
    assert_equal(stack_policy, 'have indiv. policy')


def test_simple_cloudformation_stack_during_update_default():
    cf = _create_simple_cf()
    stack_policy = _get_stack_policy_during_update(cf, False)
    assert_regexp_matches(stack_policy, '{"Statement":')
    assert_equal('Deny', json.loads(stack_policy)['Statement'][1]['Effect'])
    assert_list_equal(["Update:Replace", "Update:Delete"],
                      json.loads(stack_policy)['Statement'][1]['Action'])


def test_simple_cloudformation_stack_during_update_override_default():
    cf = _create_simple_cf()
    stack_policy = _get_stack_policy_during_update(cf, True)
    assert_regexp_matches(stack_policy, '{"Statement":')


def test_parameter_substitution():
    config_string = '''
    cloudformation {
        ConfigOne = value1
        ConfigTwo = [value2, value3]
    }
    '''
    expected = [
        {
            'ParameterKey': 'ConfigOne',
            'ParameterValue': 'value1',
            'UsePreviousValue': False
        },
        {
            'ParameterKey': 'ConfigTwo',
            'ParameterValue': 'value2,value3',
            'UsePreviousValue': False
        }
    ]
    conf = ConfigFactory.parse_string(config_string)
    converted_conf = _generate_parameters(conf)
    assert_equal(converted_conf, expected)


def test_parameter_substitution_reserved_terms():
    config_string = '''
    cloudformation {
        ConfigOne = value1
        StackName = value2
        TemplateBody = value3
        ArtifactBucket = value4
    }
    '''
    expected = [
        {
            'ParameterKey': 'ConfigOne',
            'ParameterValue': 'value1',
            'UsePreviousValue': False
        }
    ]
    conf = ConfigFactory.parse_string(config_string)
    converted_conf = _generate_parameters(conf)
    assert_equal(converted_conf, expected)


def test_get_conf_value():
    config_string = '''
    cloudformation {
        ConfigOne = value1
    }
    '''
    config = ConfigFactory.parse_string(config_string)
    assert_equal(_get_conf_value(config, 'ConfigOne'), 'value1')


def test_get_conf_value_list():
    config_string = '''
    cloudformation {
        ConfigOne = [a, b, c]
    }
    '''
    config = ConfigFactory.parse_string(config_string)
    assert_equal(_get_conf_value(config, 'ConfigOne'), 'a,b,c')


@raises(ConfigMissingException)
def test_get_conf_value_unknown():
    config_string = '''
    cloudformation {
        ConfigOne = [a, b, c]
    }
    '''
    config = ConfigFactory.parse_string(config_string)
    _get_conf_value(config, 'Unknown')


def test_generate_parameter_entry():
    config_string = '''
    cloudformation {
        ConfigOne = value1
    }
    '''
    config = ConfigFactory.parse_string(config_string)
    assert_dict_equal(_generate_parameter_entry(config, 'ConfigOne'),
                      {
                          'ParameterKey': 'ConfigOne',
                          'ParameterValue': 'value1',
                          'UsePreviousValue': False
                      })
