import string
import sys
import re
from aws_cdk import (
    Stack,
    aws_timestream as timestream,
    aws_iot as iot,
    aws_iam as iam,
    aws_logs as logs
)
from constructs import Construct
import aws_cdk as cdk

sys.path.append('../')

from customExceptions import *

class TimestreamPatternStack(Stack):

    # Defining class variables
    dimensions_list = []
    topic_sql = ""
    timestream_db_name = ""
    timestream_table_name = ""
    timestream_iot_role_name = ""
    timestream_iot_rule_name = ""
    

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Getting the context parameters 

        # Required parameters for users to set in the CLI command or cdk.json
        self.dimensions_list = self.node.try_get_context("dimensions")
        self.topic_sql = self.node.try_get_context("topic_sql")

        # Optional parameters for users to set in the CLI command or cdk.json
        self.timestream_db_name = self.node.try_get_context("timestream_db_name")
        self.timestream_table_name = self.node.try_get_context("timestream_table_name")
        self.timestream_iot_role_name = self.node.try_get_context("timestream_iot_role_name")
        self.timestream_iot_rule_name = self.node.try_get_context("timestream_iot_rule_name")

        # Perform input validation 
        self.performInputValidation()

        # Creating the timestream database 
        timestream_database = timestream.CfnDatabase(self, self.timestream_db_name, database_name=self.timestream_db_name)
        timestream_database.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating the timestream table under the database previously made
        timestream_table = timestream.CfnTable(self, self.timestream_table_name, database_name=self.timestream_db_name, 
        retention_properties={"MemoryStoreRetentionPeriodInHours": "24", "MagneticStoreRetentionPeriodInDays": "7"}, table_name=self.timestream_table_name)
        timestream_table.node.add_dependency(timestream_database)
        timestream_table.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating the role for the IoT-Timestream rule
        iot_timestream_role = iam.Role(self, self.timestream_iot_role_name, assumed_by=iam.ServicePrincipal("iot.amazonaws.com")) 
        iot_timestream_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[timestream_table.attr_arn], actions=["timestream:WriteRecords"]))
        iot_timestream_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=["*"], actions=["timestream:DescribeEndpoints"]))
        iot_timestream_role.node.add_dependency(timestream_table)
        iot_timestream_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating the dimension list based on the user input
        dimensions = [iot.CfnTopicRule.TimestreamDimensionProperty(name = dim, value = "${" + dim + "}") for dim in self.dimensions_list]

        # Creating a cloudwatch log group for topic rule's error action 
        log_group = logs.LogGroup(self, "iot_to_timestream_log_group" , log_group_name="iot_to_timestream_log_group", removal_policy=cdk.RemovalPolicy.DESTROY)
        
        iot_to_cloudwatch_logs_role = iam.Role(self, "iot_to_log_group_role", assumed_by=iam.ServicePrincipal("iot.amazonaws.com")) 
        iot_to_cloudwatch_logs_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW, resources=[log_group.log_group_arn], 
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:PutMetricFilter", "logs:PutRetentionPolicy"]))
        iot_to_cloudwatch_logs_role.node.add_dependency(log_group)
        iot_to_cloudwatch_logs_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating the IoT Topic Rule
        topic_rule = iot.CfnTopicRule(self, self.timestream_iot_rule_name, topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty( 
            actions=[iot.CfnTopicRule.ActionProperty(timestream=iot.CfnTopicRule.TimestreamActionProperty(
                database_name=self.timestream_db_name,
                dimensions=dimensions,
                role_arn=iot_timestream_role.role_arn,
                table_name=self.timestream_table_name
            ))], 
            sql=self.topic_sql,
            error_action= iot.CfnTopicRule.ActionProperty(
                cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                    log_group_name=log_group.log_group_name,
                    role_arn=iot_to_cloudwatch_logs_role.role_arn
                )
            )))
        topic_rule.node.add_dependency(timestream_database)
        topic_rule.node.add_dependency(iot_timestream_role)
        topic_rule.node.add_dependency(timestream_table)
        topic_rule.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)
    

    def performInputValidation(self):
        self.validateSql(self.topic_sql)
        self.validateDimensionList(self.dimensions_list)
        if not self.timestream_db_name:
            self.timestream_db_name = "DemoTimestreamDB"
        else:
            self.validateTimestreamResourceName(self.timestream_db_name)
        if not self.timestream_table_name:
            self.timestream_db_name = "DemoTimestreamTable"
        else:
            self.validateTimestreamResourceName(self.timestream_table_name)
        self.validateIoTtoTimestreamRoleName(self.timestream_iot_role_name)
        self.validateIoTTpoicRuleName(self.timestream_iot_rule_name)    
    
    def validateSql(self, sqlStatement):
        if not sqlStatement:
            raise NoSQL
        elif type(sqlStatement) != str: 
            raise WrongFormattedInput("The input sql statement does not have a right format. Please refer to README.md for more information.")
        return        

    def validateTimestreamResourceName(self, inputStr):
        if type(inputStr) != str:
            raise WrongFormattedInput("The provided input for Timestream resource name is not of type string.")
        elif not re.match(r'^[a-zA-Z0-9-_\.]+$', inputStr):
            raise WrongFormattedInput("String format error for Timestream resource name: Must contain letters, digits, dashes, periods or underscores.")
        elif len(inputStr) < 3 or len(inputStr) > 256:
            raise WrongLengthForInput("String length error for Timestream resource name: Must have a minimum length of 3 and a Maximum length of 256.")
        else:
            return    

    def validateIoTTpoicRuleName(self, inputStr):
        if not inputStr:
            self.timestream_iot_rule_name = "DemoIoTtoTimestreamRule"
        elif type(inputStr) != str:
            raise WrongFormattedInput("The provided input for topic rule name is not of type string.")
        elif not re.match(r'^[a-zA-Z0-9_]+$', inputStr):
            raise WrongFormattedInput("String format error: The topic rule name should be an alphanumeric string that can also contain underscore (_) characters, but no spaces.")
        else:
            return      

    def validateIoTtoTimestreamRoleName(self, inputStr):
        if not inputStr:
            self.timestream_iot_role_name = "DemoIoTtoTimestreamRole"
        elif type(inputStr) != str:
            raise WrongFormattedInput("The provided input for the IAM role name is not of type string")
        elif len(inputStr) > 64: 
            raise WrongLengthForInput("The length of the IAM role name string should not exceed 64 characters.")    
        elif not re.match(r'^[a-zA-Z0-9+=,@-_\.]+$', inputStr):
            raise WrongFormattedInput("String format error: The IAM role name should be an alphanumeric string that can also contain '+=,.@-_' characters.")
        else:
            return

    def validateDimensionList(self, dimensinList):
        if not dimensinList:
            raise NoTimestreamDimension
        elif type(dimensinList) != list:
            raise WrongFormattedInput("The provided input for the dimesnion list is not of type list.")     
        else:
            for d in dimensinList:
                if type(d) != str:
                    raise WrongFormattedInput("At least one of the provided dimensions is not of type string.")    
            return                          