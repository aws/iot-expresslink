from importlib import resources
from attr import attr
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_iot as iot,
    aws_logs as logs,
    aws_opensearchservice as opensearch,
    aws_cognito as cognito
)
from constructs import Construct
import aws_cdk as cdk
import datetime
import string
import sys
import secrets
import re

sys.path.append('../')
from customExceptions import *

class OpenSearchPatternStack(Stack):

    # Defining class variables
    topic_sql = ""
    opensearch_domain_name = ""
    opensearch_index_name = ""
    opensearch_type_name = ""
    cognito_user_pool_name = ""
    cognito_user_pool_domain_name = ""
    cognito_identity_pool_name = ""
    cognito_user_username = ""
    iot_to_opensearch_rule_name = ""
    iot_to_opensearch_role_name = ""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the context parameters

        # Required parameters for users to set in the CLI command or cdk.json
        self.topic_sql = self.node.try_get_context("topic_sql")

        # Optional parameters for users to set in the CLI command or cdk.json
        self.opensearch_domain_name = self.node.try_get_context("opensearch_domain_name")
        self.opensearch_index_name = self.node.try_get_context("opensearch_index_name")
        self.opensearch_type_name = self.node.try_get_context("opensearch_type_name")
        self.cognito_user_pool_name = self.node.try_get_context("cognito_user_pool_name")
        self.cognito_user_pool_domain_name = self.node.try_get_context("cognito_user_pool_domain_name")
        self.cognito_identity_pool_name = self.node.try_get_context("cognito_identity_pool_name")
        self.cognito_user_username = self.node.try_get_context("cognito_user_username")
        self.iot_to_opensearch_rule_name = self.node.try_get_context("iot_to_opensearch_rule_name")
        self.master_user_role_name = self.node.try_get_context("master_user_role_name")

        # Input Validation
        self.performInputValidation()

        # Creating cognito identity pool 
        identityPool = cognito.CfnIdentityPool(self, self.cognito_identity_pool_name, allow_unauthenticated_identities=False)
        identityPool.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating an IAM role as the master user for the fine-grained access control
        masterUserRole = iam.CfnRole(self, self.master_user_role_name, assume_role_policy_document={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "cognito-identity.amazonaws.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "cognito-identity.amazonaws.com:aud": identityPool.ref
                        },
                        "ForAnyValue:StringLike": {
                            "cognito-identity.amazonaws.com:amr": "authenticated"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "iot.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }) 
        masterUserRole.node.add_dependency(identityPool)
        masterUserRole.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating cognito User pool and a domain for it
        userPool = cognito.UserPool(self, self.cognito_user_pool_name)
        userPool.add_domain(id=self.cognito_user_pool_domain_name, cognito_domain=cognito.CognitoDomainOptions(
            domain_prefix=self.cognito_user_pool_domain_name))
        userPool.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating a UserPoolUser with a temporary password
        masterUser = cdk.custom_resources.AwsCustomResource(self, "UserPoolUserCreation",
            policy=cdk.custom_resources.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(effect=iam.Effect.ALLOW, actions=["cognito-idp:*"], resources=["*"])
            ]),
            on_create=cdk.custom_resources.AwsSdkCall(
                service='CognitoIdentityServiceProvider', 
                action='adminCreateUser',
                parameters={
                    "UserPoolId": userPool.user_pool_id,
                    "Username": self.cognito_user_username,
                    "TemporaryPassword": self.randomTemporaryPasswordGenerator(10)
                },
            physical_resource_id=cdk.custom_resources.PhysicalResourceId.of('userpoolcreateid' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ))
        

        # Creating a UserPoolGroup in the UserPool
        user_pool_group = cognito.CfnUserPoolGroup(self, "master-user-group", group_name="master-user-group", 
        role_arn=masterUserRole.attr_arn, user_pool_id=userPool.user_pool_id)
        user_pool_group.node.add_dependency(userPool)
        user_pool_group.node.add_dependency(masterUserRole)
        user_pool_group.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)
        
        # Attaching the user to the group
        user_to_group_attachment = cognito.CfnUserPoolUserToGroupAttachment(self, "CDK_master_user_group_attachement", 
        group_name=user_pool_group.group_name, username=self.cognito_user_username, user_pool_id=userPool.user_pool_id)
        user_to_group_attachment.node.add_dependency(user_pool_group)
        user_to_group_attachment.node.add_dependency(userPool)
        user_to_group_attachment.node.add_dependency(masterUser)
        user_to_group_attachment.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating an IAM role to grant Opensearch access to Cognito
        cognitoAccessForOpenSearchRole = iam.Role(self, "CDKCognitoAccessForOpenSearch", assumed_by=iam.ServicePrincipal("es.amazonaws.com"))
        cognitoAccessForOpenSearchRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonOpenSearchServiceCognitoAccess"))
        cognitoAccessForOpenSearchRole.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating an Opensearch domain
        domain = opensearch.Domain(self, self.opensearch_domain_name,
        domain_name=self.opensearch_domain_name,
        version=opensearch.EngineVersion.OPENSEARCH_1_2,
        node_to_node_encryption=True,
        encryption_at_rest=opensearch.EncryptionAtRestOptions(
            enabled=True
        ), 
        capacity=opensearch.CapacityConfig(
            data_nodes=3,
            data_node_instance_type="t3.small.search"
        ), 
        enforce_https=True,
        fine_grained_access_control=opensearch.AdvancedSecurityOptions(
            master_user_arn=masterUserRole.attr_arn
        ),
        cognito_dashboards_auth=opensearch.CognitoOptions(
            identity_pool_id=identityPool.ref,
            user_pool_id=userPool.user_pool_id,
            role=cognitoAccessForOpenSearchRole
        ))
        domain.add_access_policies(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[domain.domain_arn+"/*"], actions=["es:ESHttp*"], principals=[iam.AnyPrincipal()]))
        domain.node.add_dependency(identityPool)
        domain.node.add_dependency(userPool)
        domain.node.add_dependency(cognitoAccessForOpenSearchRole)
        domain.node.add_dependency(masterUserRole)
        domain.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Getting the Client ID of the opensearch client in UserPool
        userPoolClients = cdk.custom_resources.AwsCustomResource(self, "ClientIdResource",
            policy=cdk.custom_resources.AwsCustomResourcePolicy.from_sdk_calls(
                resources=[userPool.user_pool_arn]
            ),
            on_create=cdk.custom_resources.AwsSdkCall(
                service='CognitoIdentityServiceProvider', 
                action='listUserPoolClients',
                parameters={"UserPoolId" : userPool.user_pool_id},
                physical_resource_id=cdk.custom_resources.PhysicalResourceId.of(f'ClientId-{self.cognito_user_pool_domain_name}')
        ))
        userPoolClients.node.add_dependency(domain)
        clientID = userPoolClients.get_response_field('UserPoolClients.0.ClientId')

        # Changing Use default role to Choose role from token in Authentication Providers and For Role resolution, choose DENY. (Identity Pool Settigns)
        roleAttachement = cognito.CfnIdentityPoolRoleAttachment(self, "CDKIdentityPoolAttachment", 
        identity_pool_id=identityPool.ref,
        roles={},
        role_mappings={
            "role_mappings_key": cognito.CfnIdentityPoolRoleAttachment.RoleMappingProperty(
                type='Token',
                ambiguous_role_resolution='Deny',
                identity_provider=f'cognito-idp.{self.region}.amazonaws.com/{userPool.user_pool_id}:{clientID}'
            )
        })
        roleAttachement.node.add_dependency(domain)
        roleAttachement.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Changing masterUserRole to  also grant IoT access to Opensearch
        masterUserRole.policies = [iam.CfnRole.PolicyProperty(
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "iotanalytics:BatchPutMessage",
                        "Resource": f"arn:aws:iotanalytics:{self.region}:{self.account}:domain/{self.opensearch_domain_name}/*",
                        "Effect": "Allow"
                    }
                ]
            },
            policy_name="master_useriot_integration")]
        
        # Creating a cloud watch log group to capture any errors while sending the data through the IoT rule
        log_group = logs.LogGroup(self, "iot_to_opensearch_log_group" , log_group_name="iot_to_opensearch_log_group", removal_policy=cdk.RemovalPolicy.DESTROY)

        # Creating the role to access the cloudwatch log group from IoT Core
        iot_cloudwatch_log_role = iam.Role(self, "iot_cloudwatch_error_log_role", assumed_by=iam.ServicePrincipal("iot.amazonaws.com")) 
        iot_cloudwatch_log_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[log_group.log_group_arn], actions=["logs:CreateLogStream","logs:DescribeLogStreams","logs:PutLogEvents"]))
        iot_cloudwatch_log_role.node.add_dependency(log_group)
        iot_cloudwatch_log_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating the IoT Core Rule + Setting the error action to log in the cloud watch log group
        topic_rule = iot.CfnTopicRule(self, self.iot_to_opensearch_rule_name, topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty( 
            actions=[iot.CfnTopicRule.ActionProperty( open_search=iot.CfnTopicRule.OpenSearchActionProperty(
                endpoint= "https://" + domain.domain_endpoint,
                id="${newuuid()}",
                index=self.opensearch_index_name,
                role_arn=masterUserRole.attr_arn,
                type=self.opensearch_type_name
            )
        )], sql=self.topic_sql, 
            error_action = iot.CfnTopicRule.ActionProperty(
                cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                    log_group_name=log_group.log_group_name,
                    role_arn=iot_cloudwatch_log_role.role_arn
                ))
        ))
        topic_rule.node.add_dependency(domain)
        topic_rule.node.add_dependency(masterUserRole)
        topic_rule.node.add_dependency(log_group)
        topic_rule.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

    def randomTemporaryPasswordGenerator(self, length):

        source = string.ascii_letters + string.digits + string.punctuation
        password = secrets.choice(string.ascii_lowercase)
        password += secrets.choice(string.ascii_uppercase)
        password += secrets.choice(string.digits)
        password += secrets.choice(string.punctuation)

        for i in range(length-4):
            password += secrets.choice(source)

        char_list = list(password)
        secrets.SystemRandom().shuffle(char_list)
        password = ''.join(char_list)

        print(f"The temporary password created for the Cognito user is {password}\nPlease keep this password for the first login and then change it to a secure one of your own.")
        return password
    
    def performInputValidation(self):
        self.validateTopicSQL(self.topic_sql)
        self.validateOpensearchDomainName(self.opensearch_domain_name)   
        self.validateOpensearchIndexName(self.opensearch_index_name) 
        self.validateOpensearchTypeName(self.opensearch_type_name)
        self.validateCognitoUserPoolName(self.cognito_user_pool_name)
        self.validateCognitoUserPoolDomainName(self.cognito_user_pool_domain_name)
        self.validateCognitoIdentityPoolName(self.cognito_identity_pool_name)
        self.validateCognitoUserUsername(self.cognito_user_username)
        self.validateIoTRuleName(self.iot_to_opensearch_rule_name)
        self.validateIAMRoleName(self.master_user_role_name)

    def validateTopicSQL(self, input):
        if not input:
            raise NoSQL
        elif type(input) != str: 
            raise WrongFormattedInput("The input sql statement does not have a right format. Please refer to README.md for more information.")   
        return

    def validateOpensearchDomainName(self, input):
        if not input:
            self.opensearch_domain_name = "opensearch-demo-domain"
        elif type(input) != str:
            raise WrongFormattedInput("The Opensearch domain name should be of a string format.")
        elif len(input) < 3 or len(input) > 28:
            raise WrongLengthForInput("The Opensearch domain name must be between 3 and 28 characters.")
        elif not input[0].islower():
            raise WrongFormattedInput("The Opensearch domain name must start with a lowercase letter.")
        elif not re.match(r'^[a-z0-9-]+$', input):
            raise WrongFormattedInput("Valid characters for Opensearch domain name are a-z (lowercase only), 0-9, and - (hyphen).")
        else:
            return

    def validateOpensearchIndexName(self, input): 
        not_allowed_characters = [' ', ',', ':', '\"', '*', '+', '/', '\\', '|', '?', '#', '>' , '<']
        if not input:
            self.opensearch_index_name = "iot"
        elif type(input) != str:
            raise WrongFormattedInput("The Opensearch index name should be of a string format.")
        elif not input.islower():
            raise WrongFormattedInput("All letters of the Opensearch index name must be lowercase.")
        elif input[0] == "_" or input[0] == "-":
            raise WrongFormattedInput("Opensearch index names cannot begin with `_` or `-`.")
        elif any(c in input for c in not_allowed_characters):
            raise WrongFormattedInput("Opensearch index names cannot contain `spaces, commas, :, \", *, +, /, \\, |, ?, #, >, or <`.")
        else:
            return

    def validateOpensearchTypeName(self, input): 
        if not input:
            self.opensearch_type_name = "_doc"
        else:
            return

    def validateCognitoUserPoolName(self, input):
        if not input:
            self.cognito_user_pool_name = "DemoUserPool"
        elif type(input) != str:
            raise WrongFormattedInput("The Cognito UserPool name should be of a string format.")
        elif len(input) > 128:
            raise WrongLengthForInput("The Cognito UserPool name must be between one and 128 characters long.")
        elif not re.match(r'^[a-zA-Z0-9-+=,@\.]+$', input):
            raise WrongFormattedInput("The Cognito UserPool name can contain uppercase and lowercase letters, numbers, and the following special characters: + = , . @ and -")
        else:
            return

    def validateCognitoUserPoolDomainName(self, input):
        if not input:
            self.cognito_user_pool_domain_name = "iot-demo-domain"
        elif type(input) != str:
            raise WrongFormattedInput("The Cognito UserPool domain name should be of a string format.")
        elif len(input) > 63:
            raise WrongLengthForInput("The Cognito UserPool domain name must be between 1 and 63 characters long.")
        elif not re.match(r'^[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?$', input):
            raise WrongFormattedInput("The Cognito UserPool domain name can include only lowercase letters, numbers, and hyphens. Don't use a hyphen for the first or last character.")
        else:
            return

    def validateCognitoIdentityPoolName(self, input):
        if not input:
            self.cognito_identity_pool_name = "DemoIdentityPool"
        elif type(input) != str:
            raise WrongFormattedInput("The Cognito IdentityPool name should be of a string format.")
        elif len(input) > 128:
            raise WrongLengthForInput("The Cognito IdentityPool name must be between 1 and 128 characters long.")
        elif not re.match(r'^[\w\s+=,.@-]+$', input):
            raise WrongFormattedInput("Wrong format for the Cognito IdentityPool name. Please refer to README.md for more information.")
        else:
            return

    def validateCognitoUserUsername(self, input):
        if not input:
            self.cognito_user_username = "admin"
        else:
            return

    def validateIoTRuleName(self, input):
        if not input:
            self.iot_to_opensearch_rule_name = "demo_iot_opensearch_rule"
        elif type(input) != str:
            raise WrongFormattedInput("The provided input for IoT topic rule name is not of type string.")
        elif not re.match(r'^[a-zA-Z0-9-_\.]+$', input):
            raise WrongFormattedInput("The IoT topic rule name should be an alphanumeric string that can also contain underscore (_) characters, but no spaces.")
        else:
            return 

    def validateIAMRoleName(self, input):
        if not input:
            self.master_user_role_name = "demo_iot_opensearch_role"
        elif type(input) != str:
            raise WrongFormattedInput("The provided input for the IAM role name is not of type string.")
        elif len(input) > 64: 
            raise WrongLengthForInput("The length of the IAM role name string should not exceed 64 characters.")    
        elif not re.match(r'^[a-zA-Z0-9+=,@-_\.]+$', input):
            raise WrongFormattedInput("The IAM role name should be an alphanumeric string that can also contain '+=,.@-_' characters.")
        else:
            return 