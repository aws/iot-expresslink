import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk.assertions import Match

from kinesis_pattern.kinesis_pattern_stack import KinesisPatternStack
import pytest

# Setting the context for the app 
app = core.App(context={"topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
    "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
    "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
    "kinesis_delivery_stream_name": "cdk_delivery_stream",
    "kinesis_iot_role_name": "cdk_iot_kinesis_role",
    "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
    "glue_db_name": "cdk_glue_db",
    "glue_crawler_role_name": "cdk_glue_crawler_role",
    "glue_crawler_name": "cdk_glue_crawler"})

stack = KinesisPatternStack(app, "kinesis-pattern")
template = assertions.Template.from_stack(stack)

# Defining Capture objects for obtaining values in tests
bucket_ref_capture = assertions.Capture()
bucket_policy_ref = assertions.Capture()
bucket_auto_delete_object_ref = assertions.Capture()
delivery_stream_policy_name = assertions.Capture()
delivery_stream_role_ref = assertions.Capture()
iot_to_kinesis_role_ref = assertions.Capture()
iot_to_kinesis_role_policy_ref = assertions.Capture()
glue_crawler_role_ref = assertions.Capture()
glue_crawler_role_policy = assertions.Capture()
log_group_ref = assertions.Capture()
delivery_stream_logicalID = assertions.Capture()
glueDB_logicalID = assertions.Capture()

# Testing the resources' creation and properties

def test_bucket_creation():
    template.has_resource("AWS::S3::Bucket", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::S3::Bucket",1)

def test_bucket_properties():
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {"Status": "Enabled"}
    })  

def test_bucket_policy_creation():
    template.resource_count_is("AWS::S3::BucketPolicy",1)

def test_bucket_policy_properties():

    template.has_resource_properties("AWS::S3::BucketPolicy", {
        "Bucket": {"Ref": bucket_ref_capture}, 
    })

    template.has_resource_properties("AWS::S3::BucketPolicy", {
        "PolicyDocument": {
            "Statement": [{
            "Action": [ "s3:GetBucket*", "s3:List*", "s3:DeleteObject*"],
            "Effect": "Allow",
            "Principal":  Match.any_value(),
            "Resource": [
                {
                    "Fn::GetAtt": [
                    bucket_ref_capture.as_string(),
                    "Arn"
                    ]
                },
                {
                    "Fn::Join": [
                    "",
                    [ {
                        "Fn::GetAtt": [
                        bucket_ref_capture.as_string(),
                        "Arn"
                        ]
                    },
                    "/*"
                    ]]
                }]
            }],
            "Version": Match.any_value()
    }
    })


def test_delivery_stream_role_properties():
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "firehose.amazonaws.com"
                }
            }
            ],
            "Version": Match.any_value()
        }
    })

def test_delivery_stream_role_policy_properties():
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [
            {
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:GetBucketLocation",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject"
            ],
            "Effect": "Allow",
            "Resource": [
                { "Fn::GetAtt": [ bucket_ref_capture.as_string(), "Arn"]},
                {
                "Fn::Join": [
                "",
                [{ "Fn::GetAtt": [ bucket_ref_capture.as_string(), "Arn" ]},
                "/*"
                ]]}
            ]
            }],
            "Version": Match.any_value()
            },
            "PolicyName": delivery_stream_policy_name,
            "Roles": [{ "Ref": delivery_stream_role_ref }]
    })   

def test_iot_to_kinesis_role_properties():
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

def test_iot_to_kinesis_role_policy_properties():
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [{
            "Action": [
                "firehose:PutRecord",
                "firehose:PutRecordBatch"
            ],
            "Effect": "Allow",
            "Resource": {
                "Fn::GetAtt": [
                delivery_stream_logicalID,
                "Arn"
                ]
            }
            }],
            "Version": Match.any_value()
    },
        "Roles": [{ "Ref": iot_to_kinesis_role_ref }]
    })        

def test_log_group_creation():
    template.has_resource("AWS::Logs::LogGroup", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Logs::LogGroup",2)

def test_log_group_properties():
    template.has_resource_properties("AWS::Logs::LogGroup", {
        "LogGroupName": "Kinesis_deliverystream_to_s3_logs",
        "RetentionInDays": 731
    })

def test_log_stream_creation():
    template.has_resource("AWS::Logs::LogStream", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Logs::LogStream",1)

def test_log_stream_properties():
    template.has_resource_properties("AWS::Logs::LogStream", {
        "LogGroupName": {
            "Ref": log_group_ref
        },
        "LogStreamName": "Kinesis_deliverystream_to_s3_log_stream"
    })    


def test_delivery_stream_creation():
    template.has_resource("AWS::KinesisFirehose::DeliveryStream", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::KinesisFirehose::DeliveryStream",1)

def test_delivery_stream_properties():
    template.has_resource_properties("AWS::KinesisFirehose::DeliveryStream", {
        "DeliveryStreamName": app.node.try_get_context("kinesis_delivery_stream_name"),
        "S3DestinationConfiguration": {
            "BucketARN": {
                "Fn::GetAtt": [
                bucket_ref_capture.as_string(),
                "Arn"
                ]
            },
            "CloudWatchLoggingOptions": {
                "Enabled": True,
                "LogGroupName": {
                    "Ref": log_group_ref.as_string()
                },
                "LogStreamName": {
                    "Ref": Match.any_value()
                }
            },
            "RoleARN": {
                "Fn::GetAtt": [
                delivery_stream_role_ref.as_string(),
                "Arn"
                ]
            }
        }
    })  

def test_iot_rule_creation():
    template.has_resource("AWS::IoT::TopicRule", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete" })
    template.resource_count_is("AWS::IoT::TopicRule",1)

def test_iot_rule_properties():
    template.has_resource_properties("AWS::IoT::TopicRule", {
        "TopicRulePayload": {
            "Actions": [
            {
                "Firehose": {
                    "BatchMode": False,
                    "DeliveryStreamName": app.node.try_get_context("kinesis_delivery_stream_name"),
                    "RoleArn": {
                        "Fn::GetAtt": [
                        iot_to_kinesis_role_ref.as_string(),
                        "Arn"
                        ]
                    }
                }
            }
            ],
            "Sql": app.node.try_get_context("topic_sql")
        }
    })

def test_glue_database_creation():
    template.has_resource("AWS::Glue::Database", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Glue::Database",1)

def test_glue_database_properties():
    template.has_resource_properties("AWS::Glue::Database", {
        "DatabaseInput": {
            "Description": "Glue database",
            "Name": app.node.try_get_context("glue_db_name")
        }
    }) 

def test_glue_crawler_role_properties():
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "glue.amazonaws.com"
                }
            }],
            "Version": Match.any_value()
        }
    })   

def test_glue_crawler_role_policy_properties():
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [
            {
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Effect": "Allow",
            "Resource": {
                "Fn::Join": [
                    "",
                    [
                        {
                            "Fn::GetAtt": [
                                bucket_ref_capture.as_string(),
                                "Arn"
                            ]
                        },
                    "*"
                    ]
                ]
            }
            }
            ],
            "Version": Match.any_value()
        },
        "Roles": [{"Ref": glue_crawler_role_ref}]
    })     

def test_glue_crawler_creation():
    template.has_resource("AWS::Glue::Crawler", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Glue::Crawler",1)

def test_glue_crawler_properties():
    template.has_resource_properties("AWS::Glue::Crawler", {
        "Role": {
            "Fn::GetAtt": [
            glue_crawler_role_ref.as_string(),
            "Arn"
            ]
        },
        "Targets": {
            "S3Targets": [
            {
                "Path": {
                    "Fn::Join": [
                    "",
                    [
                    "s3://",
                    {
                        "Ref": bucket_ref_capture.as_string()
                    }
                    ]
                    ]
                }
            }
            ]
        },
        "DatabaseName": app.node.try_get_context("glue_db_name")
    })                 

# Testing dependencies between the resources  

def test_delivery_stream_dependencies():
    template.has_resource("AWS::KinesisFirehose::DeliveryStream", {
        "DependsOn": [
        bucket_auto_delete_object_ref,
        bucket_policy_ref,
        bucket_ref_capture.as_string()
        ]
    })

def test_delivery_stream_dependencies():
    template.has_resource("AWS::KinesisFirehose::DeliveryStream", {
        "DependsOn": [
        bucket_auto_delete_object_ref,
        bucket_policy_ref,
        bucket_ref_capture.as_string()
        ]
    }) 

def test_iot_to_kinesis_role_dependencies():
    template.has_resource("AWS::IAM::Role", {
        "DependsOn": [
        delivery_stream_logicalID.as_string()
        ]
    }) 

def test_iot_topic_rule_dependencies():
    template.has_resource("AWS::IoT::TopicRule", {
        "DependsOn": [
        delivery_stream_logicalID.as_string(),
        iot_to_kinesis_role_policy_ref,
        iot_to_kinesis_role_ref.as_string()
        ]
    })

def test_glue_crawler_role_dependencies():
    template.has_resource("AWS::IAM::Role", {
        "DependsOn": [
        bucket_auto_delete_object_ref.as_string(),
        bucket_policy_ref.as_string(),
        bucket_ref_capture.as_string()
        ]
    })    

def test_glue_crawler_dependencies():
    template.has_resource("AWS::Glue::Crawler", {
        "DependsOn": [
        glue_crawler_role_policy,
        glue_crawler_role_ref.as_string(),
        glueDB_logicalID,
        bucket_auto_delete_object_ref.as_string(),
        bucket_policy_ref.as_string(),
        bucket_ref_capture.as_string()
        ]
    })    

# Testing input validation process

def test_no_sql():
    test_app = core.App(context= {
        "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"No sql statemtnt .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)   

def test_wrong_sql_format():
    test_app = core.App(context= {
        "topic_sql": ["SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'"],
        "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"The input sql statement does not have a right format. .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)

def test_wrong_bucket_name_format():
    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "cdk_kinesis_bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"Wrong formatted input for s3 bucket name. .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)

    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "xn--bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"Wrong formatted input for s3 bucket name. .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)

    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "x" * 70,
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"Bucket names must be between 3 .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)    

def test_wrong_delivery_stream_format():
    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery@stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"String format error for delivery stream name: .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)   
        
def test_wrong_topic_rule_name_format():
    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"String format error: The topic rule name .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)  

def test_wrong_iam_role_name_format():
    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_!glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"String format error: The IAM role name should be .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
        "kinesis_delivery_stream_role_name": "c" * 70,
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "cdk_glue_db",
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"The length of the IAM role name .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)        

def test_wrong_glue_db_name_format():
    test_app = core.App(context= {
        "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-kinesis-test'",
        "kinesis_destination_bucket_name": "cdk-kinesis-bucket",
        "kinesis_delivery_stream_role_name": "cdk_kinesis_delivery_stream_role",
        "kinesis_delivery_stream_name": "cdk_delivery_stream",
        "kinesis_iot_role_name": "cdk_iot_kinesis_role",
        "kinesis_iot_rule_name": "cdk_to_kinesis_rule",
        "glue_db_name": "c" * 256,
        "glue_crawler_role_name": "cdk_glue_crawler_role",
        "glue_crawler_name": "cdk_glue_crawler"
    })
    with pytest.raises(Exception, match=r"The length of the Glue database .*"):
        stack = KinesisPatternStack(test_app, "kinesis-pattern")
        template = assertions.Template.from_stack(stack)                                               