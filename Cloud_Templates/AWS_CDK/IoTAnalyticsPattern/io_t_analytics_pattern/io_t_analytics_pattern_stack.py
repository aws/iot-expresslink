from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_iot as iot,
    aws_iotanalytics as iotanalytics,
    aws_s3 as s3,
    aws_logs as logs
)
from constructs import Construct
import aws_cdk as cdk
import re
import sys

sys.path.append('../')

from customExceptions import *

class IoTAnalyticsPatternStack(Stack):

    # Defining the class variables
    topic_sql = ""
    analytics_channel_name = ""
    analytics_datastore_name = ""
    analytics_dataset_name = ""
    analytics_pipeline_name = ""
    analytics_iot_role_name = ""
    analytics_iot_rule_name = ""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Getting the context parameters

        # Required parameters for users to set in the CLI command or cdk.json
        self.topic_sql = self.node.try_get_context("topic_sql")

        # Optional parameters for users to set in the CLI command or cdk.json
        self.analytics_channel_name = self.node.try_get_context("analytics_channel_name")
        self.analytics_datastore_name = self.node.try_get_context("analytics_datastore_name")
        self.analytics_dataset_name = self.node.try_get_context("analytics_dataset_name")
        self.analytics_pipeline_name = self.node.try_get_context("analytics_pipeline_name")
        self.analytics_iot_role_name = self.node.try_get_context("analytics_iot_role_name")
        self.analytics_iot_rule_name = self.node.try_get_context("analytics_iot_rule_name")

        # Perform input validation 
        self.performInputValidation()                

        # Creating an IoT Analytics Channel
        analytics_channel = iotanalytics.CfnChannel(self, self.analytics_channel_name, channel_name=self.analytics_channel_name) 
        analytics_channel.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating an IoT Analytics Datastore
        analytics_datastore = iotanalytics.CfnDatastore(self, self.analytics_datastore_name, datastore_name=self.analytics_datastore_name,
        datastore_storage=iotanalytics.CfnDatastore.DatastoreStorageProperty(
            service_managed_s3={}
        ),
        retention_period=iotanalytics.CfnDatastore.RetentionPeriodProperty(
            number_of_days=30,
            unlimited=False
        ))
        analytics_datastore.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating an IoT Analytics Dataset
        analytics_dataset = iotanalytics.CfnDataset(self, self.analytics_dataset_name, actions=[iotanalytics.CfnDataset.ActionProperty(
            action_name="QueryDatastoreCDK",
            query_action=iotanalytics.CfnDataset.QueryActionProperty(
                sql_query= f'''SELECT * FROM {analytics_datastore.datastore_name}'''
            )
        )])
        analytics_dataset.node.add_dependency(analytics_datastore)
        analytics_dataset.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating an Iot Analytics Pipeline
        analytics_pipeline = iotanalytics.CfnPipeline(self, self.analytics_pipeline_name, pipeline_name=self.analytics_pipeline_name, pipeline_activities=[
            iotanalytics.CfnPipeline.ActivityProperty(
                channel=iotanalytics.CfnPipeline.ChannelProperty(
                channel_name=analytics_channel.channel_name,
                name=analytics_channel.channel_name,
                next=analytics_datastore.datastore_name
            ),
            datastore=iotanalytics.CfnPipeline.DatastoreProperty(
                datastore_name=analytics_datastore.datastore_name,
                name=analytics_datastore.datastore_name
            )
        )])
        analytics_pipeline.node.add_dependency(analytics_datastore)
        analytics_pipeline.node.add_dependency(analytics_channel)
        analytics_pipeline.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)


        # Creating the role for the IoT-Analytics rule
        channel_arn = f"arn:aws:iotanalytics:{self.region}:{self.account}:channel/{analytics_channel.channel_name}"
        iot_analytics_role = iam.Role(self, self.analytics_iot_role_name, assumed_by=iam.ServicePrincipal("iot.amazonaws.com")) 
        iot_analytics_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[channel_arn], actions=["iotanalytics:BatchPutMessage"]))
        iot_analytics_role.node.add_dependency(analytics_channel)
        iot_analytics_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating a cloudwatch log group for topic rule's error action 
        log_group = logs.LogGroup(self, "iot_to_analytics_log_group" , log_group_name="iot_to_analytics_log_group", removal_policy=cdk.RemovalPolicy.DESTROY)
        
        iot_to_cloudwatch_logs_role = iam.Role(self, "iot_to_analytics_log_group_role", assumed_by=iam.ServicePrincipal("iot.amazonaws.com")) 
        iot_to_cloudwatch_logs_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW, resources=[log_group.log_group_arn], 
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:PutMetricFilter", "logs:PutRetentionPolicy"]))
        iot_to_cloudwatch_logs_role.node.add_dependency(log_group)
        iot_to_cloudwatch_logs_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)


        # Creating the IoT Core Rule 
        topic_rule = iot.CfnTopicRule(self, self.analytics_iot_rule_name, topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty( 
            actions=[iot.CfnTopicRule.ActionProperty( iot_analytics=iot.CfnTopicRule.IotAnalyticsActionProperty(
                channel_name=analytics_channel.channel_name,
                role_arn=iot_analytics_role.role_arn,
            )
        )], 
        sql=self.topic_sql,
        error_action= iot.CfnTopicRule.ActionProperty(
            cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                log_group_name=log_group.log_group_name,
                role_arn=iot_to_cloudwatch_logs_role.role_arn
                )
            )))

        topic_rule.node.add_dependency(analytics_channel)
        topic_rule.node.add_dependency(iot_analytics_role)
        topic_rule.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)


    def performInputValidation(self): 
        self.validateTopicSQL(self.topic_sql)
        self.validateAnalyticsChannelName(self.analytics_channel_name) 
        self.validateAnalyticsDatasetName(self.analytics_dataset_name)
        self.validateAnalyticsDatastoreName(self.analytics_datastore_name)
        self.validateAnalyticsPipelineName(self.analytics_pipeline_name)
        self.validateRoleName(self.analytics_iot_role_name)
        self.validateIoTRuleName(self.analytics_iot_rule_name)

    def validateTopicSQL(self, sqlStatement):
        if not sqlStatement:
            raise NoSQL
        elif type(sqlStatement) != str: 
            raise WrongFormattedInput("The input sql statement does not have a right format. Please refer to README.md for more information.")   
        return

    def validateAnalyticsChannelName(self, channelName):
        if not channelName:
            self.analytics_channel_name = "demo_iot_channel"
        else:  
            if len(channelName) < 1 or len(channelName) > 128:
                raise WrongLengthForInput("Not a valid input for channel name: The channel name must contain 1-128 characters.")  
            elif not re.match(r'^[a-zA-Z0-9_]+$', channelName):
                raise WrongFormattedInput("String format error for channel name: Valid characters are a-z, A-Z, 0-9, and _ (underscore)")   
            return     

    def validateAnalyticsDatasetName(self, datasetName):
        if not datasetName:
            self.analytics_dataset_name = "demo_iot_dataset"
        else: 
            if len(datasetName) < 1 or len(datasetName) > 128:
                raise WrongLengthForInput("Not a valid input for dataset name: The dataset name must contain 1-128 characters.")   
            elif not re.match(r'^[a-zA-Z0-9_]+$', datasetName):
                 raise WrongFormattedInput("String format error for dataset name: Valid characters are a-z, A-Z, 0-9, and _ (underscore)")   
            return 

    def validateAnalyticsDatastoreName(self, datastoreName):
        if not datastoreName:
            self.analytics_datastore_name = "demo_iot_datastore"
        else: 
            if not re.match(r'^[a-zA-Z0-9_]+$', datastoreName):
                raise WrongFormattedInput("String format error for datastore name: Valid characters are a-z, A-Z, 0-9, and _ (underscore)")   
            return 

    def validateAnalyticsPipelineName(self, pipelineName):
        if not pipelineName:
            self.analytics_pipeline_name = "demo_iot_pipeline"
        else: 
            if not re.match(r'^[a-zA-Z0-9_]+$', pipelineName):
                raise WrongFormattedInput("String format error for pipeline name: Valid characters are a-z, A-Z, 0-9, and _ (underscore)")   
            return 

    def validateRoleName(self, roleName):
        if not roleName:
            self.analytics_iot_role_name = "demo_iot_iotanalytics_role"
        elif type(roleName) != str:
            raise WrongFormattedInput("The provided input for the IAM role name is not of type string")
        elif len(roleName) > 64: 
            raise WrongLengthForInput("The length of the IAM role name string should not exceed 64 characters.")    
        elif not re.match(r'^[a-zA-Z0-9+=,@-_\.]+$', roleName):
            raise WrongFormattedInput("String format error: The IAM role name should be an alphanumeric string that can also contain '+=,.@-_' characters.")
        else:
            return  

    def validateIoTRuleName(self, ruleName):
        if not ruleName:
            self.analytics_iot_rule_name = "demo_to_iotanalytics_rule"
        elif type(ruleName) != str:
            raise WrongFormattedInput("The provided input for topic rule name is not of type string")
        elif not re.match(r'^[a-zA-Z0-9_]+$', ruleName):
            raise WrongFormattedInput("String format error: The topic rule name should be an alphanumeric string that can also contain underscore (_) characters, but no spaces.")
        else:
            return                                    