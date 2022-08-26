from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_kinesisfirehose as kinesisfirehose,
    aws_iot as iot,
    aws_iam as iam,
    aws_logs as logs,
    aws_glue as glue
)
from constructs import Construct
import aws_cdk as cdk
import re
import sys

sys.path.append('../')
from common.inputValidation import *

# Defining class variables
topic_sql = ""
kinesis_destination_bucket_name = ""
kinesis_delivery_stream_role_name = ""
kinesis_delivery_stream_name = ""
kinesis_iot_role_name = ""
kinesis_iot_rule_name = ""
glue_db_name = ""
glue_crawler_role_name = ""
glue_crawler_name = ""

class KinesisPatternStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the context parameters

        # Required parameters for users to set in the CLI command or cdk.json
        self.topic_sql = self.node.try_get_context("topic_sql")

        # Optional parameters for users to set in the CLI command or cdk.json
        self.kinesis_destination_bucket_name = self.node.try_get_context("kinesis_destination_bucket_name")
        self.kinesis_delivery_stream_role_name = self.node.try_get_context("kinesis_delivery_stream_role_name")
        self.kinesis_delivery_stream_name = self.node.try_get_context("kinesis_delivery_stream_name")
        self.kinesis_iot_role_name = self.node.try_get_context("kinesis_iot_role_name")
        self.kinesis_iot_rule_name = self.node.try_get_context("kinesis_iot_rule_name")
        self.glue_db_name = self.node.try_get_context("glue_db_name")
        self.glue_crawler_role_name = self.node.try_get_context("glue_crawler_role_name")
        self.glue_crawler_name = self.node.try_get_context("glue_crawler_name")

        # Performing input validation before starting resource creation
        self.performInputValidation()

        # Create a bucket for as delivery stream's destination 
        bucket = s3.Bucket(self, self.kinesis_destination_bucket_name, versioned=True, removal_policy=cdk.RemovalPolicy.DESTROY, auto_delete_objects=True)

        # Creating a role for the delivery stream 
        firehose_role = iam.Role(self, self.kinesis_delivery_stream_role_name, assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"))
        firehose_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[bucket.bucket_arn, bucket.bucket_arn + "/*"], actions=["s3:AbortMultipartUpload",
                "s3:GetBucketLocation","s3:GetObject", "s3:ListBucket", "s3:ListBucketMultipartUploads", "s3:PutObject"]))
        firehose_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating a cloud watch log group to capture any errors while sending the data from the delivery stream to the bucket
        log_group = logs.LogGroup(self, "Kinesis_deliverystream_to_s3_logs" , log_group_name="Kinesis_deliverystream_to_s3_logs", removal_policy=cdk.RemovalPolicy.DESTROY)
        log_stream = logs.LogStream(self, "Kinesis_deliverystream_to_s3_log_stream", log_group=log_group ,log_stream_name="Kinesis_deliverystream_to_s3_log_stream", removal_policy=cdk.RemovalPolicy.DESTROY)

        # Creating the delivery stream
        delivery_stream = kinesisfirehose.CfnDeliveryStream(self, self.kinesis_delivery_stream_name, delivery_stream_name=self.kinesis_delivery_stream_name, 
        s3_destination_configuration=kinesisfirehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
            bucket_arn=bucket.bucket_arn,
            role_arn= firehose_role.role_arn,
            # the properties below are optional
            cloud_watch_logging_options=kinesisfirehose.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                enabled=True,
                log_group_name=log_group.log_group_name,
                log_stream_name=log_stream.log_stream_name
            )
        ))
        delivery_stream.node.add_dependency(bucket)
        delivery_stream.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating the role for the IoT Kinesis rule
        iot_kinesis_role = iam.Role(self, self.kinesis_iot_role_name, assumed_by=iam.ServicePrincipal("iot.amazonaws.com")) 
        iot_kinesis_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[delivery_stream.attr_arn], actions=["firehose:PutRecord", "firehose:PutRecordBatch"]))
        iot_kinesis_role.node.add_dependency(delivery_stream)
        iot_kinesis_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating a cloudwatch log group for topic rule's error action 
        rule_log_group = logs.LogGroup(self, "iot_to_kinesis_log_group" , log_group_name="iot_to_kinesis_log_group", removal_policy=cdk.RemovalPolicy.DESTROY)
        
        iot_to_cloudwatch_logs_role = iam.Role(self, "iot_to_kinesis_log_group_role", assumed_by=iam.ServicePrincipal("iot.amazonaws.com")) 
        iot_to_cloudwatch_logs_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW, resources=[rule_log_group.log_group_arn], 
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:PutMetricFilter", "logs:PutRetentionPolicy"]))
        iot_to_cloudwatch_logs_role.node.add_dependency(rule_log_group)
        iot_to_cloudwatch_logs_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating the IoT rule with action = Kinesis Firehose
        topic_rule = iot.CfnTopicRule(self, self.kinesis_iot_rule_name, topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty( 
            actions=[iot.CfnTopicRule.ActionProperty( firehose=iot.CfnTopicRule.FirehoseActionProperty(
                delivery_stream_name=self.kinesis_delivery_stream_name,
                role_arn=iot_kinesis_role.role_arn,

                # the properties below are optional
                batch_mode=False
            )
        )], sql=self.topic_sql,
            aws_iot_sql_version = '2016-03-23',
            error_action= iot.CfnTopicRule.ActionProperty(
            cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                log_group_name=rule_log_group.log_group_name,
                role_arn=iot_to_cloudwatch_logs_role.role_arn
                )
            )))
        topic_rule.node.add_dependency(delivery_stream)
        topic_rule.node.add_dependency(iot_kinesis_role)
        topic_rule.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        #create an Athena/Glue Database
        glue_database = glue.CfnDatabase(
            self,
            id=self.glue_db_name,
            catalog_id=cdk.Aws.ACCOUNT_ID,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                description=f"Glue database",
                name=self.glue_db_name,
            )
        )
        glue_database.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)

        # Creating a role for the glue crawler
        glue_s3_role = iam.Role(self, self.glue_crawler_role_name, assumed_by=iam.ServicePrincipal("glue.amazonaws.com")) 
        glue_s3_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=[bucket.bucket_arn+"*"], actions=["s3:GetObject", "s3:PutObject"]))
        glue_s3_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"))
        glue_s3_role.node.add_dependency(bucket)
        glue_s3_role.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)


        # Creating an Athena/Glue crawler for the s3 bucket
        s3_path = f"s3://{bucket.bucket_name}"
        crawler = glue.CfnCrawler(self, self.glue_crawler_name, role=glue_s3_role.role_arn, targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[glue.CfnCrawler.S3TargetProperty(
                path=s3_path
            )]), database_name = self.glue_db_name)
        crawler.node.add_dependency(glue_s3_role)
        crawler.node.add_dependency(glue_database)
        crawler.node.add_dependency(bucket)
        crawler.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)        

    # Performing input validation on the inpute parameters of the stack
    def performInputValidation(self):
        self.validateTopicSQL(self.topic_sql)
        self.validateBucketName(self.kinesis_destination_bucket_name)   
        self.validateDeliveryStreamName(self.kinesis_delivery_stream_name) 
        self.validateIoTRuleName(self.kinesis_iot_rule_name)
        self.validateGlueDBName(self.glue_db_name)
        self.validateGlueCrawlerName(self.glue_crawler_name)
        self.validateIAMRoleName(self.glue_crawler_role_name, resource="crawler")
        self.validateIAMRoleName(self.kinesis_iot_role_name, resource="iot")
        self.validateIAMRoleName(self.kinesis_delivery_stream_role_name, resource="delivery_stream")

    def validateTopicSQL(self, input):
        if not input:
            raise NoSQL
        elif type(input) != str: 
            raise WrongFormattedInput("The input sql statement does not have a right format. Please refer to README.md for more information.")   
        return

    def validateBucketName(self, input):
        if not input:
            self.kinesis_destination_bucket_name = "demo_kinesis_bucket"
        elif type(input) != str:
            raise WrongFormattedInput("The provided input for s3 bucket name is not of type string")  
        else:
            checkInputLength(self, 3, 63, input, "bucket") 
            checkInputPattern(self, r'(?!(^xn--|-s3alias$))^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$', input, "bucket")    

    def validateDeliveryStreamName(self, input):
        if not input:
            self.kinesis_delivery_stream_name = "demo_delivery_stream"
        else: 
            if type(input) != str:
                raise WrongFormattedInput("The provided input for delivery stream name is not of type string")
            else:
                checkInputPattern(self, r'^[a-zA-Z0-9-_\.]+$', input, "delivery stream") 

    def validateIoTRuleName(self, input):
        if not input:
            self.kinesis_iot_rule_name = "demo_to_kinesis_rule"
        elif type(input) != str:
            raise WrongFormattedInput("The provided input for topic rule name is not of type string")
        else:
            checkInputPattern(self, r'^[a-zA-Z0-9-_\.]+$', input, "IoT rule") 

    def validateIAMRoleName(self, input, resource):
        if not input:
            if resource == 'crawler':
                self.glue_crawler_role_name = "demo_glue_crawler_role"
            elif resource == 'iot':
                self.kinesis_iot_role_name = "demo_iot_kinesis_role"
            elif resource == 'delivery_stream': 
                self.kinesis_delivery_stream_role_name = "demo_kinesis_delivery_stream_role"  
        elif type(input) != str:
            raise WrongFormattedInput("The provided input for the IAM role name is not of type string")
        else:
            checkInputLength(self, 1, 64, input, "IAM role")
            checkInputPattern(self, r'^[a-zA-Z0-9+=,@-_\.]+$', input, "IAM role") 

    def validateGlueDBName(self, input):
        if not input:
            self.glue_db_name = "demo_glue_db"
        elif type(input) != str:
            raise WrongFormattedInput("The provided input for the Glue database name is not of type string") 
        else:
            checkInputLength(self, 1, 255, input, "Gue database")  

    def validateGlueCrawlerName(self, input):
        if not input:
            self.glue_crawler_name = "demo_glue_crawler"
        else:
            return