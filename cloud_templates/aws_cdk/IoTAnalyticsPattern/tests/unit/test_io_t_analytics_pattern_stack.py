import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk.assertions import Match
import pytest

from io_t_analytics_pattern.io_t_analytics_pattern_stack import IoTAnalyticsPatternStack

app = core.App(context= {"topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-analytics-test'",
    "analytics_channel_name": "cdk_iot_channel",
    "analytics_datastore_name": "cdk_iot_datastore",
    "analytics_dataset_name": "cdk_iot_dataset",
    "analytics_pipeline_name": "cdk_iot_pipeline",
    "analytics_iot_role_name": "cdk_iot_analytics_role",
    "analytics_iot_rule_name": "cdk_to_analytics_rule"})

stack = IoTAnalyticsPatternStack(app, "io-t-analytics-pattern")
template = assertions.Template.from_stack(stack)

# Defining Capture objects for obtaining values in tests
iam_policy_ref = assertions.Capture()
iam_role_ref = assertions.Capture()
iot_datastore_ref = assertions.Capture()
iot_channel_ref = assertions.Capture()

# Testing the resources' creation and properties

def test_analytics_channel_created():
    template.has_resource("AWS::IoTAnalytics::Channel", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::IoTAnalytics::Channel", 1)

def test_analytics_channel_properties():
    template.has_resource_properties("AWS::IoTAnalytics::Channel", {
        "ChannelName": app.node.try_get_context("analytics_channel_name")
    })    

def test_analytics_datastore_created():
    template.has_resource("AWS::IoTAnalytics::Datastore", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::IoTAnalytics::Datastore", 1)

def test_analytics_datastore_properties():
    template.has_resource_properties("AWS::IoTAnalytics::Datastore", {
        "DatastoreName": app.node.try_get_context("analytics_datastore_name"),
        "DatastoreStorage": {"ServiceManagedS3": {}}
    })   

def test_analytics_dataset_created():
    template.has_resource("AWS::IoTAnalytics::Dataset", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::IoTAnalytics::Dataset", 1)

def test_analytics_dataset_properties():
    template.has_resource_properties("AWS::IoTAnalytics::Dataset", {
        "Actions": [{
            "ActionName": "QueryDatastoreCDK",
            "QueryAction": {
                "SqlQuery": f'SELECT * FROM {app.node.try_get_context("analytics_datastore_name")}'
            }
        }]
    })   

def test_analytics_pipeline_created():
    template.has_resource("AWS::IoTAnalytics::Pipeline", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::IoTAnalytics::Pipeline", 1)

def test_analytics_pipeline_properties():
    template.has_resource_properties("AWS::IoTAnalytics::Pipeline", {
        "PipelineActivities": [{
            "Channel": {
                "ChannelName": app.node.try_get_context("analytics_channel_name"),
                "Name": app.node.try_get_context("analytics_channel_name"),
                "Next": app.node.try_get_context("analytics_datastore_name")
            },
            "Datastore": {
                "DatastoreName": app.node.try_get_context("analytics_datastore_name"),
                "Name": app.node.try_get_context("analytics_datastore_name")
            }
        }],
        "PipelineName": app.node.try_get_context("analytics_pipeline_name")
    })      

def test_iam_role_properties():
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "iot.amazonaws.com"
                }
            }],
            "Version": Match.any_value()
        }
    })  

def test_iam_policy_properties():
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [
            {
                "Action": "iotanalytics:BatchPutMessage",
                "Effect": "Allow",
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
                    f":channel/{app.node.try_get_context('analytics_channel_name')}"
                    ]
                    ]
                }
            }
            ],
            "Version": Match.any_value()
        },
        "PolicyName": iam_policy_ref,
        "Roles": [
        {
            "Ref": iam_role_ref
        }
        ]
    }) 

def test_iot_topic_rule_created():
    template.has_resource("AWS::IoT::TopicRule", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::IoT::TopicRule", 1)

def test_iot_topic_rule_properties():
    template.has_resource_properties("AWS::IoT::TopicRule", {
        "TopicRulePayload": {
            "Actions": [{
                "IotAnalytics": {
                    "ChannelName": app.node.try_get_context("analytics_channel_name"),
                    "RoleArn": {
                        "Fn::GetAtt": [
                        iam_role_ref.as_string(),
                        "Arn"
                    ]
                    }
                }
            }],
            "Sql": app.node.try_get_context("topic_sql")
        }
    })   

# Testing dependencies between the resources

def test_dataset_dependencies():
    template.has_resource("AWS::IoTAnalytics::Dataset", {
        "DependsOn": [
            iot_datastore_ref
        ]
    }) 

def test_pipeline_dependencies():
    template.has_resource("AWS::IoTAnalytics::Pipeline", {
        "DependsOn": [
            iot_channel_ref,
            iot_datastore_ref.as_string()
        ]
    })   

def test_iam_role_dependencies():
    template.has_resource("AWS::IAM::Role", {
        "DependsOn": [
            iot_channel_ref.as_string()
        ]
    })  

def test_iam_policy_dependencies():
    template.has_resource("AWS::IAM::Policy", {
        "DependsOn": [
            iot_channel_ref.as_string()
        ]
    }) 

def test_topic_rule_dependencies():
    template.has_resource("AWS::IoT::TopicRule", {
        "DependsOn": [
            iam_policy_ref.as_string(),
            iam_role_ref.as_string(),
            iot_channel_ref.as_string()
        ]
    })               

# Testing input validations

def test_no_sql(): 
    test_app = core.App(context= {
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"No sql statemtnt .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)

def test_wrong_sql_format(): 
    test_app = core.App(context= {
        "topic_sql": ["SELECT * FROM 'topic"],
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"The input sql statement does not have a right format.*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)

def test_wrong_format_channel_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk-iot-channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input pattern .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)        

def test_wrong_length_channel_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "x" * 129,
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input length .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack) 

def test_wrong_format_dataset_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk-iot-dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input pattern .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)        

def test_wrong_length_dataset_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "x" * 129,
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input length .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)         

def test_wrong_format_datastore_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk-iot-datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input pattern .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack) 
        
def test_wrong_format_pipeline_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk-iot-pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input pattern .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)  

def test_wrong_format_role_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_!analytics_role",
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input pattern .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)                 
       
def test_wrong_length_role_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "x" * 65,
        "analytics_iot_rule_name": "cdk_to_analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input length .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)   

def test_wrong_format_rule_name(): 
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'topic'",
        "analytics_channel_name": "cdk_iot_channel",
        "analytics_datastore_name": "cdk_iot_datastore",
        "analytics_dataset_name": "cdk_iot_dataset",
        "analytics_pipeline_name": "cdk_iot_pipeline",
        "analytics_iot_role_name": "cdk_iot_analytics_role",
        "analytics_iot_rule_name": "cdk to analytics_rule"
    })
    with pytest.raises(Exception, match=r"Invalid input pattern .*"):
        stack = IoTAnalyticsPatternStack(test_app, "io-t-analytics-pattern")
        template = assertions.Template.from_stack(stack)                          