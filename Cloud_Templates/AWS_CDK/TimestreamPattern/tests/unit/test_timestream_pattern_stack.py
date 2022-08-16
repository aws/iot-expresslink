import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk.assertions import Match
import pytest

from timestream_pattern.timestream_pattern_stack import TimestreamPatternStack

# Setting the context for the app 
app = core.App(context={
    "topic_sql": "SELECT temperature, pressure, humidity FROM 'EL-timestream_test'",
    "dimensions": ["device_id"],
    "timestream_db_name": "cdk_db",
    "timestream_table_name": "cdk_table",
    "timestream_iot_role_name": "cdk_timestream_role",
    "timestream_iot_rule_name": "cdk_to_timetream_rule"
})

stack = TimestreamPatternStack(app, "timestream-pattern")
template = assertions.Template.from_stack(stack)

# Defining Capture objects for obtaining values in tests
table_ref = assertions.Capture()
db_ref = assertions.Capture()
policy_ref = assertions.Capture()
role_ref = assertions.Capture()


# Testing the resources' creation and properties

def test_timestream_database_creation():
    template.has_resource("AWS::Timestream::Database", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Timestream::Database", 1)

def test_timestream_database_properties():
    template.has_resource_properties("AWS::Timestream::Database", {
        "DatabaseName": app.node.try_get_context("timestream_db_name")
    })    

def test_timestream_table_creation():
    template.has_resource("AWS::Timestream::Table", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::Timestream::Table", 1)

def test_timestream_table_properties():
    template.has_resource_properties("AWS::Timestream::Table", {
        "DatabaseName": app.node.try_get_context("timestream_db_name"),
        "TableName" : app.node.try_get_context("timestream_table_name"),
        "RetentionProperties": { "MemoryStoreRetentionPeriodInHours": "24", "MagneticStoreRetentionPeriodInDays": "7"}
    })    

def test_timesream_role_creation():
    template.has_resource("AWS::IAM::Role", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})

def test_timestream_role_properties():
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {"Statement": [{ "Action": "sts:AssumeRole", "Effect": "Allow", 
        "Principal": { "Service": "iot.amazonaws.com"}}], "Version": Match.any_value()}
    })

def test_timestream_role_policy_properties():
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [
            {
                "Action": "timestream:WriteRecords",
                "Effect": "Allow",
                "Resource": {
                    "Fn::GetAtt": [
                    table_ref,
                    "Arn"
                    ]
                }
            },
            {
                "Action": "timestream:DescribeEndpoints",
                "Effect": "Allow",
                "Resource": "*"
            }
            ],
            "Version": Match.any_value()
        },
        "PolicyName": policy_ref,
        "Roles": [
        {
            "Ref": role_ref
        }
        ]
    })        

def test_iot_topic_rule_creation():
    template.has_resource("AWS::IoT::TopicRule", {"DeletionPolicy":"Delete", "UpdateReplacePolicy":"Delete"})
    template.resource_count_is("AWS::IoT::TopicRule", 1)

def test_iot_topic_rule_properties():
    dimesnsion_list = []
    for d in app.node.try_get_context("dimensions"):
        dimesnsion_list.append({
            "Name": d,
            "Value": "${" + d + "}"
        })
    template.has_resource_properties("AWS::IoT::TopicRule", {
        "TopicRulePayload": {
            "Actions": [{
                "Timestream": {
                    "DatabaseName": app.node.try_get_context("timestream_db_name"),
                    "Dimensions": dimesnsion_list,
                    "RoleArn": {
                        "Fn::GetAtt": [
                        role_ref.as_string(),
                        "Arn"
                        ]
                    },
                    "TableName": app.node.try_get_context("timestream_table_name")
                }
            }],
            "Sql": app.node.try_get_context("topic_sql")
    }
    }) 
    
# Testing dependencies between the resources  

def test_timestream_table_dependencies():
    template.has_resource("AWS::Timestream::Table", {
        "DependsOn": [
            db_ref
        ]
    })

def test_timestream_role_dependencies():
    template.has_resource("AWS::IAM::Role", {
        "DependsOn": [
            table_ref.as_string()
        ]
    })    

def test_timestream_policy_dependencies():
    template.has_resource("AWS::IAM::Policy", {
        "DependsOn": [
            table_ref.as_string()
        ]
    })

def test_iot_topic_rule_dependencies():
    template.has_resource("AWS::IoT::TopicRule", {
        "DependsOn": [
            db_ref.as_string(),
            table_ref.as_string(),
            policy_ref.as_string(),
            role_ref.as_string()
        ]
    })        

# Testing input validation process

def test_no_sql():
    test_app = core.App(context= {
        "topic_sql": "",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"No sql statemtnt .*"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)

def test_no_dimension():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"No dimesnsion is provided. *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)

def test_wrong_dimension():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": "device_id",
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"The provided input for the dimesnion list is not of type list."):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": [2,"id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"At least one of the provided dimensions is not of type string."):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)    

def test_wrong_sql():
    test_app = core.App(context= {
        "topic_sql": ["SELECT * FROM 'EL-timestream_test'"],
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"The input sql statement does not have a right format. *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)   

def test_wrong_db_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": True,
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"The provided input for Timestream resource name is not of type string."):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"String length error for Timestream resource name: *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db!",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"String format error for Timestream resource name: *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)                    

def test_wrong_table_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": ["cdk_table"],
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"The provided input for Timestream resource name is not of type string."):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "x" * 300,
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"String length error for Timestream resource name: *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table@",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"String format error for Timestream resource name: *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)

def test_wrong_topic_rule_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": ["cdk_to_timetream_rule"]
    })
    with pytest.raises(Exception, match=r"The provided input for topic rule name is not of type string."):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk_timestream_role",
        "timestream_iot_rule_name": "cdk_to timetream_rule"
    })
    with pytest.raises(Exception, match=r"String format error: The topic rule name *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)

def test_wrong_iam_role_name():
    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "c" * 65,
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"The length of the IAM role name string should not exceed 64 characters."):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack) 

    test_app = core.App(context= {
        "topic_sql": "SELECT * FROM 'EL-timestream_test'",
        "dimensions": ["device_id"],
        "timestream_db_name": "cdk_db",
        "timestream_table_name": "cdk_table",
        "timestream_iot_role_name": "cdk&timestream_role",
        "timestream_iot_rule_name": "cdk_to_timetream_rule"
    })
    with pytest.raises(Exception, match=r"String format error: The IAM role name *"):
        stack = TimestreamPatternStack(test_app, "timestream-pattern")
        template = assertions.Template.from_stack(stack)   