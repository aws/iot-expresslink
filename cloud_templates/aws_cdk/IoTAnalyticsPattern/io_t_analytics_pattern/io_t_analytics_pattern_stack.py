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
from enum import Enum

sys.path.append('../')
from common.inputValidation import *

class StorageType(Enum):
    SERVICE_MANAGED = "service_managed"
    CUSTOMER_MANAGED = "customer_managed"

class FileFormat(Enum):
    JSON = "json"
    PARQUET = "parquet"

class IoTAnalyticsPatternStack(Stack):

    # Defining the class variables
    topic_sql = ""
    analytics_channel_name = ""
    analytics_datastore_name = ""
    analytics_dataset_name = ""
    analytics_pipeline_name = ""
    analytics_iot_role_name = ""
    analytics_iot_rule_name = ""
    # By default, IoT analytics resources use service_managed storage and Json file format
    channel_storage_type = StorageType.SERVICE_MANAGED
    datastore_storage_type = StorageType.SERVICE_MANAGED
    file_format_configuration = FileFormat.JSON

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Getting the context parameters

        # Required context parameters
        self.topic_sql = self.node.try_get_context("topic_sql")

        # Optional context parameters
        self.analytics_channel_name = self.node.try_get_context("analytics_channel_name")
        self.analytics_datastore_name = self.node.try_get_context("analytics_datastore_name")
        self.analytics_dataset_name = self.node.try_get_context("analytics_dataset_name")
        self.analytics_pipeline_name = self.node.try_get_context("analytics_pipeline_name")
        self.analytics_iot_role_name = self.node.try_get_context("analytics_iot_role_name")
        self.analytics_iot_rule_name = self.node.try_get_context("analytics_iot_rule_name")

        # Perform input validation 
        self.performInputValidation()                

        # Checking for advanced settings
        self.checkAdvSettings()

        # Getting the IoT Analytics Channel
        analytics_channel = self.createChannel()

        # Creating an IoT Analytics Datastore
        analytics_datastore = self.createDataStore()

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
        aws_iot_sql_version = '2016-03-23',
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
            checkInputLength(self, 1, 128, channelName, "channel")
            checkInputPattern(self, r'^[a-zA-Z0-9_]+$', channelName, "channel") 

    def validateAnalyticsDatasetName(self, datasetName):
        if not datasetName:
            self.analytics_dataset_name = "demo_iot_dataset"
        else: 
            checkInputLength(self, 1, 128, datasetName, "dataset") 
            checkInputPattern(self, r'^[a-zA-Z0-9_]+$', datasetName, "dataset")  

    def validateAnalyticsDatastoreName(self, datastoreName):
        if not datastoreName:
            self.analytics_datastore_name = "demo_iot_datastore"
        else: 
            checkInputPattern(self, r'^[a-zA-Z0-9_]+$', datastoreName, "datastore")

    def validateAnalyticsPipelineName(self, pipelineName):
        if not pipelineName:
            self.analytics_pipeline_name = "demo_iot_pipeline"
        else: 
            checkInputPattern(self, r'^[a-zA-Z0-9_]+$', pipelineName, "pipeline")

    def validateRoleName(self, roleName):
        if not roleName:
            self.analytics_iot_role_name = "demo_iot_iotanalytics_role"
        elif type(roleName) != str:
            raise WrongFormattedInput("The provided input for the IAM role name is not of type string")
        else: 
            checkInputLength(self, 1, 64, roleName, "IAM role")
            checkInputPattern(self, r'^[a-zA-Z0-9+=,@-_\.]+$', roleName, "IAMrole")

    def validateIoTRuleName(self, ruleName):
        if not ruleName:
            self.analytics_iot_rule_name = "demo_to_iotanalytics_rule"
        elif type(ruleName) != str:
            raise WrongFormattedInput("The provided input for topic rule name is not of type string")
        else: 
            checkInputPattern(self, r'^[a-zA-Z0-9_]+$', ruleName, "IoT Rule")                                

    def checkAdvSettings(self): 
        channel_storage_type = self.node.try_get_context("channel_storage_type")
        datastore_storage_type = self.node.try_get_context("datastore_storage_type")
        file_format = self.node.try_get_context("file_format_configuration")
        
        if channel_storage_type == StorageType.CUSTOMER_MANAGED.value:
            self.channel_storage_type = StorageType.CUSTOMER_MANAGED

        if datastore_storage_type == StorageType.CUSTOMER_MANAGED.value:
            self.datastore_storage_type = StorageType.CUSTOMER_MANAGED

        if file_format == FileFormat.PARQUET.value:
            self.file_format_configuration = FileFormat.PARQUET

    def createChannel(self):

        analytics_channel = ""

        if self.channel_storage_type == StorageType.SERVICE_MANAGED:
            analytics_channel = iotanalytics.CfnChannel(self, self.analytics_channel_name, channel_name=self.analytics_channel_name) 
            analytics_channel.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)
        elif self.channel_storage_type == StorageType.CUSTOMER_MANAGED:
            # Creating a bucket for channel storage 
            channel_bucket = s3.Bucket(self, "iot-analytics-channel-storage", versioned=True, removal_policy=cdk.RemovalPolicy.DESTROY, auto_delete_objects=True)

            # Creating an IAM Role to give iotanalytics access to the bucket 
            channel_storage_bucket_role = iam.Role(self, "iot_analytics_channel_storage_bucket_role", assumed_by=iam.ServicePrincipal("iotanalytics.amazonaws.com"))
            channel_storage_bucket_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[channel_bucket.bucket_arn, channel_bucket.bucket_arn + "/*"], 
            actions=["s3:GetBucketLocation","s3:GetObject", "s3:ListBucket", "s3:PutObject"]))
            channel_storage_bucket_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

            analytics_channel = iotanalytics.CfnChannel(self, self.analytics_channel_name, channel_name=self.analytics_channel_name,
            channel_storage = iotanalytics.CfnChannel.ChannelStorageProperty(
                customer_managed_s3 = iotanalytics.CfnChannel.CustomerManagedS3Property(
                    bucket = channel_bucket.bucket_name,
                    role_arn= channel_storage_bucket_role.role_arn
                )
            ))
            analytics_channel.node.add_dependency(channel_bucket)
            analytics_channel.node.add_dependency(channel_storage_bucket_role)
            analytics_channel.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)
        else: 
            raise Exception("An error occured while getting the channel's storage type.")

        return analytics_channel

    def createDataStore(self):
        analytics_datastore = ""

        if self.file_format_configuration == FileFormat.JSON:
            file_format_config = iotanalytics.CfnDatastore.FileFormatConfigurationProperty(
                json_configuration={}
            )

        if self.file_format_configuration == FileFormat.PARQUET:
            file_format_config = iotanalytics.CfnDatastore.FileFormatConfigurationProperty(
                    parquet_configuration=iotanalytics.CfnDatastore.ParquetConfigurationProperty(
                        schema_definition=iotanalytics.CfnDatastore.SchemaDefinitionProperty(
                            columns=[iotanalytics.CfnDatastore.ColumnProperty(name=column["name"],type=column["type"]) for column in self.node.try_get_context("parquet_file_format_schema_columns")]
                        )
                ))

        if self.datastore_storage_type == StorageType.SERVICE_MANAGED:
            analytics_datastore = analytics_datastore = iotanalytics.CfnDatastore(self, self.analytics_datastore_name, datastore_name=self.analytics_datastore_name,
            datastore_storage=iotanalytics.CfnDatastore.DatastoreStorageProperty(
                service_managed_s3={}
                ))
            analytics_datastore.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        elif self.datastore_storage_type == StorageType.CUSTOMER_MANAGED:
            # Creating a bucket for channel storage 
            datastore_bucket = s3.Bucket(self, "iot-analytics-datastore-storage", versioned=True, removal_policy=cdk.RemovalPolicy.DESTROY, auto_delete_objects=True)

            # Creating an IAM Role to give iotanalytics access to the bucket 
            datastore_storage_bucket_role = iam.Role(self, "iot_analytics_datastore_storage_bucket_role", assumed_by=iam.ServicePrincipal("iotanalytics.amazonaws.com"))
            datastore_storage_bucket_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[datastore_bucket.bucket_arn, datastore_bucket.bucket_arn + "/*"], 
            actions=["s3:GetBucketLocation","s3:GetObject", "s3:ListBucket", "s3:PutObject"]))
            datastore_storage_bucket_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

            analytics_datastore = iotanalytics.CfnDatastore(self, self.analytics_datastore_name, datastore_name=self.analytics_datastore_name,
            datastore_storage = iotanalytics.CfnDatastore.DatastoreStorageProperty(
                customer_managed_s3=iotanalytics.CfnDatastore.CustomerManagedS3Property(
                    bucket=datastore_bucket.bucket_name,
                    role_arn=datastore_storage_bucket_role.role_arn
                )),
            file_format_configuration=file_format_config
            )
            analytics_datastore.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)
            analytics_datastore.node.add_dependency(datastore_bucket)
            analytics_datastore.node.add_dependency(datastore_storage_bucket_role)
        else: 
            raise Exception("An error occured while getting the datastore's storage type.")

        return analytics_datastore