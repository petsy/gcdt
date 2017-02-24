# -*- coding: utf-8 -*-

"""Helper to create IAM parts of cloud formation templates
"""

from __future__ import unicode_literals, print_function
import troposphere
from troposphere.iam import Role, PolicyType, ManagedPolicy
from troposphere.s3 import Bucket, BucketPolicy

from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole


class IAMRoleAndPolicies(object):
    """Class to generate IAM roles and policies
    Note: gcdt.iam IAMRoleAndPolicies(template, role_name_prefix, role_principals, role_path)
    is used in many cloudformation.py templates!
    """

    VERSION_IAM = "2012-10-17"

    def __init__(self, template, role_name_prefix, role_principals, role_path):
        """
        Init
        :param template: The cloudformation template
        :param role_name_prefix: Prefix for the name of the role inside cloudformation
        :param role_principals: The principal of the roles (the one who can use it eg. lambda)
        :param role_path: The path of the role (overview)
        :return: None
        """
        self.__template = template
        self.__role_name_prefix = role_name_prefix
        self.__role_principals = role_principals
        self.__role_path = role_path
        self.__roles_list = []

    @property
    def roles_list(self):
        """
        Returns list of role references which were created with this instance.
        List can be used to reference a global policy.
        :return: List of role references created
        """
        return self.__roles_list

    def name_build(self, name, is_policy=False, prefix=True):
        """
        Build name from prefix and name + type
        :param name: Name of the role/policy
        :param is_policy: True if policy should be added as suffix
        :param prefix: True if prefix should be added
        :return: Joined name
        """
        str = name

        # Add prefix
        if prefix:
            str = self.__role_name_prefix + str

        # Add policy suffix
        if is_policy:
            str = str + "-policy"

        return str

    def name_strip(self, name, is_policy=False, prefix=True):
        """
        Transforms name to AWS valid characters and adds prefix and type
        :param name: Name of the role/policy
        :param is_policy: True if policy should be added as suffix
        :param prefix: True if prefix should be added
        :return: Transformed and joined name
        """
        str = self.name_build(name, is_policy, prefix)
        str = str.title()
        str = str.replace('-', '')
        return str

    def build_policy(self, name, statements, roles, is_managed_policy=False):
        """
        Generate policy for IAM cloudformation template
        :param name: Name of the policy
        :param statements: The "rules" the policy should have
        :param roles: The roles associated with this policy
        :param is_managed_policy: True if managed policy
        :return: Ref to new policy
        """
        if is_managed_policy:
            policy = ManagedPolicy(
                self.name_strip(name, True),
                PolicyDocument={
                    "Version": self.VERSION_IAM,
                    "Statement": statements,
                },
                Roles=roles,
                Path=self.__role_path,
            )
        else:
            policy = PolicyType(
                self.name_strip(name, True),
                PolicyName=self.name_strip(name, True),
                PolicyDocument={
                    "Version": self.VERSION_IAM,
                    "Statement": statements,
                },
                Roles=roles,
            )

        self.__template.add_resource(policy)
        return policy

    def build_policy_bucket(self, bucket, name, statements):
        """
        Generate bucket policy for S3 bucket
        :param bucket: The bucket to attach policy to
        :param name: The name of the bucket (to generate policy name from it)
        :param statements: The "rules" the policy should have
        :return: Ref to new policy
        """

        policy = self.__template.add_resource(
            BucketPolicy(
                self.name_strip(name, True, False),
                Bucket=troposphere.Ref(bucket),
                DependsOn=[
                    troposphere.Name(bucket)
                ],
                PolicyDocument=Policy(
                    Version=self.VERSION_IAM,
                    Statement=statements
                )
            )
        )

        return policy

    def build_role(self, name, policies=False):
        """
        Generate role for IAM cloudformation template
        :param name: Name of role
        :param policies: List of policies to attach to this role (False = none)
        :return: Ref to new role
        """
        # Build role template
        if policies:
            role = self.__template.add_resource(
                Role(
                    self.name_strip(name),
                    AssumeRolePolicyDocument=Policy(
                        Version=self.VERSION_IAM,
                        Statement=[
                            Statement(
                                Effect=Allow,
                                Principal=Principal(
                                    "Service", self.__role_principals
                                ),
                                Action=[AssumeRole],
                            )
                        ]
                    ),
                    Path=self.__role_path,
                    ManagedPolicyArns=policies,
                ))
            # Add role to list for default policy
            self.__roles_list.append(troposphere.Ref(role))
        else:
            role = self.__template.add_resource(
                Role(
                    self.name_strip(name),
                    AssumeRolePolicyDocument=Policy(
                        Version=self.VERSION_IAM,
                        Statement=[
                            Statement(
                                Effect=Allow,
                                Principal=Principal(
                                    "Service", self.__role_principals
                                ),
                                Action=[AssumeRole],
                            )
                        ]
                    ),
                    Path=self.__role_path,
                ))
            # Add role to list for default policy
            self.__roles_list.append(troposphere.Ref(role))

        return role

    def build_bucket(self, name, lifecycle_configuration=False,
                     use_plain_name=False):
        """
        Generate S3 bucket statement
        :param name: Name of the bucket
        :param lifecycle_configuration: Additional lifecycle configuration (default=False)
        :param use_plain_name: Just use the given name and do not add prefix
        :return: Ref to new bucket
        """
        if use_plain_name:
            name_aws = name_bucket = name
            name_aws = name_aws.title()
            name_aws = name_aws.replace('-', '')
        else:
            name_aws = self.name_strip(name, False, False)
            name_bucket = self.name_build(name)

        if lifecycle_configuration:
            return self.__template.add_resource(
                Bucket(
                    name_aws,
                    BucketName=name_bucket,
                    LifecycleConfiguration=lifecycle_configuration
                )
            )
        else:
            return self.__template.add_resource(
                Bucket(
                    name_aws,
                    BucketName=name_bucket,
                )
            )
