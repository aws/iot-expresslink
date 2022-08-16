import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk.assertions import Match
import pytest

from open_search_pattern.open_search_pattern_stack import OpenSearchPatternStack

# Setting the context for the app 
app = core.App(context={
    "topic_sql": "SELECT * FROM 'Opensearch_demo'",
    "opensearch_domain_name": "cdk-opensearch-domain",
    "opensearch_index_name": "measurements",
    "opensearch_type_name": "_doc",
    "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
    "master_user_role_name": "masterUserRole",
    "cognito_user_pool_name" : "CDKUserPool",
    "cognito_identity_pool_name": "CDKIdentityPool",
    "cognito_user_pool_domain_name": "cdk-iot-domain",
    "cognito_user_username": "admin"
})

stack = OpenSearchPatternStack(app, "open-search-pattern")
template = assertions.Template.from_stack(stack)

# Defining Capture objects for obtaining values in tests
userPool_ref_capture = assertions.Capture()
userpooluser_lambda_ref_capture = assertions.Capture()
userPool_group_name = assertions.Capture()
userPool_group_ref_capture = assertions.Capture()
userPool_domain_ref_capture = assertions.Capture()
fineGrainedRole_ref_capture = assertions.Capture()
identity_pool_ref_capture = assertions.Capture()
cognitoAccessForOpenSearch_role_ref_capture = assertions.Capture()
opensearch_domain_ref_capture = assertions.Capture()
opensearch_domain_access_policy_ref_capture = assertions.Capture()
custom_clientIdResource_ref_capture = assertions.Capture()
log_group_ref_capture = assertions.Capture()
log_group_role_ref_capture = assertions.Capture()
log_group_policy_ref_capture = assertions.Capture()
userPoolUserCreation_ref_capture = assertions.Capture()
userPoolUserCreationCustomResourcePolicy_ref_capture = assertions.Capture()
masterUserRole_ref_capture = assertions.Capture()

# Testing the resources' creation and properties

def test_identity_pool_creation():
    template.has_resource("AWS::Cognito::IdentityPool", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Cognito::IdentityPool",1)

def test_identity_pool_properties():
    template.has_resource_properties("AWS::Cognito::IdentityPool", {
        "AllowUnauthenticatedIdentities": False
    })  

def test_masterUser_IAM_role_properties():
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Version": Match.any_value(),
            "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": "cognito-identity.amazonaws.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": {
                            "Ref": app.node.try_get_context("cognito_identity_pool_name")
                        }
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
        },
        "Policies": [{
            "PolicyDocument": {
                "Version": Match.any_value(),
                "Statement": [
                    {
                        "Action": "iotanalytics:BatchPutMessage",
                        "Resource": {
                            "Fn::Join": [
                            "",
                            [
                                "arn:aws:iotanalytics:",
                                {
                                    "Ref": "AWS::Region"
                                },
                                ":",
                                {
                                    "Ref": "AWS::AccountId"
                                },
                                f':domain/{app.node.try_get_context("opensearch_domain_name")}/*'
                            ]
                            ]
                        },
                        "Effect": "Allow"
                    }
                ]
            },
            "PolicyName": Match.any_value()
        }]
    }) 

def test_user_pool_creation():
    template.has_resource("AWS::Cognito::UserPool", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Cognito::UserPool",1)

def test_user_pool_properties():
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "AccountRecoverySetting": {
        "RecoveryMechanisms": [
        {
        "Name": "verified_phone_number",
        "Priority": 1
        },
        {
        "Name": "verified_email",
        "Priority": 2
        }
        ]
        },
        "AdminCreateUserConfig": {
        "AllowAdminCreateUserOnly": True
        }
    })

def test_user_pool_domain_creation():
    template.has_resource("AWS::Cognito::UserPoolDomain", {})
    template.resource_count_is("AWS::Cognito::UserPoolDomain",1)

def test_user_pool_domain_properties():
    template.has_resource_properties("AWS::Cognito::UserPoolDomain", {
        "Domain": app.node.try_get_context("cognito_user_pool_domain_name"),
        "UserPoolId": {
            "Ref": userPool_ref_capture
        }
    })

def test_user_pool_user_creation():
     template.has_resource("Custom::AWS", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})

def test_user_pool_user_properties():
    template.has_resource_properties("Custom::AWS", {
        "ServiceToken": {
            "Fn::GetAtt": [
            userpooluser_lambda_ref_capture,
            "Arn"
            ]
        },
        "Create": Match.any_value(),
        "InstallLatestAwsSdk": True
    }) 

def test_user_pool_user_group_creation():
     template.has_resource("AWS::Cognito::UserPoolGroup", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
     template.resource_count_is("AWS::Cognito::UserPoolGroup", 1)

def test_user_pool_user_group_properties():
    template.has_resource_properties("AWS::Cognito::UserPoolGroup", {
        "UserPoolId": {
            "Ref": userPool_ref_capture.as_string()
        },
        "GroupName": userPool_group_name,
        "RoleArn": {
            "Fn::GetAtt": [
            app.node.try_get_context("master_user_role_name"),
            "Arn"
            ]
        }
    }) 

def test_userPoolUserToGroupAttachment_creation():
     template.has_resource("AWS::Cognito::UserPoolUserToGroupAttachment", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
     template.resource_count_is("AWS::Cognito::UserPoolUserToGroupAttachment", 1)

def test_userPoolUserToGroupAttachment_properties():
    template.has_resource_properties("AWS::Cognito::UserPoolUserToGroupAttachment", {
        "GroupName": userPool_group_name.as_string(),
        "Username": app.node.try_get_context("cognito_user_username"),
        "UserPoolId": {
            "Ref": userPool_ref_capture.as_string()
        }
    }) 

def test_CognitoAccessForOpenSearch_role_properties():
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "es.amazonaws.com"
                }
            }],
            "Version": Match.any_value()
        },
        "ManagedPolicyArns": [
        {
            "Fn::Join": [
            "",
            [
                "arn:",
                {
                    "Ref": "AWS::Partition"
                },
                ":iam::aws:policy/AmazonOpenSearchServiceCognitoAccess"
            ]]
        }]
    }) 

def test_opensearch_domain_creation():
    template.has_resource("AWS::OpenSearchService::Domain", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::OpenSearchService::Domain",1)

def test_opensearch_domain_properties():
    template.has_resource_properties("AWS::OpenSearchService::Domain", {
        "AdvancedSecurityOptions": {
            "Enabled": True,
            "InternalUserDatabaseEnabled": False,
            "MasterUserOptions": {
                "MasterUserARN": {
                    "Fn::GetAtt": [
                        fineGrainedRole_ref_capture,
                        "Arn"
                    ]
                }
            }
        },
        "ClusterConfig": {
            "DedicatedMasterEnabled": False,
            "InstanceCount": Match.any_value(),
            "InstanceType": Match.any_value(),
            "ZoneAwarenessEnabled": False
        },
        "CognitoOptions": {
            "Enabled": True,
            "IdentityPoolId": {
                "Ref": identity_pool_ref_capture
            },
            "RoleArn": {
                "Fn::GetAtt": [
                cognitoAccessForOpenSearch_role_ref_capture,
                "Arn"
                ]
            },
            "UserPoolId": {
                "Ref": userPool_ref_capture.as_string()
            }
        },
        "DomainEndpointOptions": {
            "EnforceHTTPS": True,
            "TLSSecurityPolicy": Match.any_value()
        },
        "DomainName": app.node.try_get_context("opensearch_domain_name"),
        "EBSOptions": {
            "EBSEnabled": True,
            "VolumeSize": Match.any_value(),
            "VolumeType": Match.any_value()
        },
        "EncryptionAtRestOptions": {
            "Enabled": True
        },
        "EngineVersion": Match.any_value(),
        "LogPublishingOptions": {},
        "NodeToNodeEncryptionOptions": {
            "Enabled": True
        }
    })

def test_opensearch_access_policy_properties():
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [
            {
            "Action": "es:UpdateDomainConfig",
            "Effect": "Allow",
            "Resource": {
                "Fn::GetAtt": [
                opensearch_domain_ref_capture,
                "Arn"
                ]
            }
            }
            ],
            "Version": Match.any_value()
        },
        "PolicyName": opensearch_domain_access_policy_ref_capture,
        "Roles": [
        {
            "Ref": Match.any_value()
        }
        ]
    })

def test_IdentityPoolRoleAttachment_creation():
     template.has_resource("AWS::Cognito::IdentityPoolRoleAttachment", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
     template.resource_count_is("AWS::Cognito::IdentityPoolRoleAttachment", 1)

def test_IdentityPoolRoleAttachment_properties():
    template.has_resource_properties("AWS::Cognito::IdentityPoolRoleAttachment", {
        "IdentityPoolId": {
            "Ref": identity_pool_ref_capture.as_string()
        },
        "RoleMappings": {
            "role_mappings_key": {
                "AmbiguousRoleResolution": "Deny",
                "IdentityProvider": {
                    "Fn::Join": [
                        "",
                        [
                        "cognito-idp.",
                        {
                            "Ref": "AWS::Region"
                        },
                        ".amazonaws.com/",
                        {
                            "Ref": userPool_ref_capture.as_string()
                        },
                        ":",
                        {
                            "Fn::GetAtt": [
                            custom_clientIdResource_ref_capture,
                            "UserPoolClients.0.ClientId"
                            ]
                        }
                        ]]
                },
                "Type": "Token"
            }
        },
        "Roles": {}
    }) 

def test_log_group_creation():
    template.has_resource("AWS::Logs::LogGroup", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Logs::LogGroup",1)

def test_log_group_properties():
    template.has_resource_properties("AWS::Logs::LogGroup", {
        "LogGroupName": "iot_to_opensearch_log_group",
        "RetentionInDays": Match.any_value()
    })  

def test_log_group_role_properties():
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
        "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "iot.amazonaws.com"
            }
        }
        ],
        "Version": Match.any_value()
        }
    })  

def test_log_group_policy_properties():
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [
            {
                "Action": [
                    "logs:CreateLogStream",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents"
                ],
                "Effect": "Allow",
                "Resource": {
                    "Fn::GetAtt": [
                    log_group_ref_capture,
                    "Arn"
                    ]
                }
            }
            ],
            "Version": Match.any_value()
        },
        "PolicyName": log_group_policy_ref_capture,
        "Roles": [
        {
            "Ref": log_group_role_ref_capture
        }
        ]
    }) 

def test_iot_rule_creation():
    template.has_resource("AWS::IoT::TopicRule", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::IoT::TopicRule",1)

def test_iot_rule_properties():
    template.has_resource_properties("AWS::IoT::TopicRule", {
        "TopicRulePayload": {
            "Actions": [
            {
                "OpenSearch": {
                    "Endpoint": {
                        "Fn::Join": [
                        "",
                        [
                        "https://",
                        {
                            "Fn::GetAtt": [
                            opensearch_domain_ref_capture.as_string(),
                            "DomainEndpoint"
                            ]
                        }
                        ]
                        ]
                    },
                    "Id": "${newuuid()}",
                    "Index": app.node.try_get_context("opensearch_index_name"),
                    "RoleArn": {
                        "Fn::GetAtt": [
                        fineGrainedRole_ref_capture.as_string(),
                        "Arn"
                        ]
                    },
                    "Type": app.node.try_get_context("opensearch_type_name")
                }
            }
            ],
            "ErrorAction": {
                "CloudwatchLogs": {
                    "LogGroupName": {
                        "Ref": log_group_ref_capture.as_string()
                    },
                    "RoleArn": {
                        "Fn::GetAtt": [
                        log_group_role_ref_capture.as_string(),
                        "Arn"
                        ]
                    }
                }
            },
            "Sql": app.node.try_get_context("topic_sql")
        }
    })  

# Testing dependencies between the resources  

def test_masterUser_role_dependencies():
    template.has_resource("AWS::IAM::Role", {
        "DependsOn": [
        identity_pool_ref_capture.as_string()
        ]
    })

def test_userPoolUserToGroupAttachment_dependencies():
    template.has_resource("AWS::Cognito::UserPoolUserToGroupAttachment", {
        "DependsOn": [
        userPool_domain_ref_capture,
        userPool_ref_capture.as_string(),
        userPool_group_ref_capture,
        userPoolUserCreationCustomResourcePolicy_ref_capture,
        userPoolUserCreation_ref_capture
        ]
    })

def test_opensearch_domain_dependencies():
    template.has_resource("AWS::OpenSearchService::Domain", {
        "DependsOn": [
        cognitoAccessForOpenSearch_role_ref_capture.as_string(),
        identity_pool_ref_capture.as_string(),
        userPool_domain_ref_capture.as_string(),
        userPool_ref_capture.as_string(),
        masterUserRole_ref_capture
        ]
    })    

# Testing input validation process

def test_no_sql():
    test_app = core.App(context= {
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "measurements",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"No sql statemtnt .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

def test_wrong_sql():
    test_app = core.App(context= {
        "topic_sql": ["SELECT * FROM 'Opensearch_demo'"],
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "measurements",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The input sql statement does not have a right format. .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

def test_wrong_opensearch_domain():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": ["cdk-opensearch-domain"],
        "opensearch_index_name": "measurements",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Opensearch domain name should be of a string format."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "x" * 30,
        "opensearch_index_name": "measurements",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Opensearch domain name must be between 3 and 28 characters."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "Domain",
        "opensearch_index_name": "measurements",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Opensearch domain name must start with a lowercase letter."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "domain_iot",
        "opensearch_index_name": "measurements",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"Valid characters for Opensearch domain .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

def test_wrong_opensearch_index():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "Index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"All letters of the Opensearch index name must be lowercase."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "_myindex",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"Opensearch index names cannot begin with `_` or `-`."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "my\\index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"Opensearch index names cannot contain .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

def test_wrong_userPool_domain_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "X" * 64,
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Cognito UserPool domain name must be between 1 and 63 characters long."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "-cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Cognito UserPool domain name can include .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "Cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Cognito UserPool domain name can include .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

def test_wrong_userPool_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "c" * 129,
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Cognito UserPool name must be between one and 128 characters long."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDK#UserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Cognito UserPool name can contain .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

def test_wrong_identityPool_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "c" * 129,
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The Cognito IdentityPool name must be between 1 and 128 characters long."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDK#IdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"Wrong format for the Cognito IdentityPool name. .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack)       

def test_wrong_iot_rule_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_@iot_opensearchFineGrained_rule",
        "master_user_role_name": "masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The IoT topic rule name .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack)  

def test_wrong_iam_role_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "#masterUserRole",
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The IAM role name .*"):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'Opensearch_demo'",
        "opensearch_domain_name": "cdk-opensearch-domain",
        "opensearch_index_name": "index",
        "opensearch_type_name": "_doc",
        "iot_to_opensearch_rule_name": "cdk_iot_opensearchFineGrained_rule",
        "master_user_role_name": "c" * 65,
        "cognito_user_pool_name" : "CDKUserPool",
        "cognito_identity_pool_name": "CDKIdentityPool",
        "cognito_user_pool_domain_name": "cdk-iot-domain",
        "cognito_user_username": "admin"
    })
    with pytest.raises(Exception, match=r"The length of the IAM role name string should not exceed 64 characters."):
        stack = OpenSearchPatternStack(test_app, "open-search-pattern")
        template = assertions.Template.from_stack(stack)  