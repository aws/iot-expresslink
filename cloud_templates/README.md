# Data ingestion and visualization with AWS CloudFormation templates

These CloudFormation templates are prepared to deploy to the cloud and visualize the data coming from your Expresslink. To learn more about AWS CloudFormation, see [**What is CloudFormation?**](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)

These templates are designed in four different patterns to ingest your IoT data using: 

1.  Amazon Timestream
<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-Timstream.png" alt="alt text"/></center>
</br>

In this structure, first the MQTT messages are captured in IoT Core and then pushed to Amazon Timestream by using IoT Core built rule which will provide a table view of the data to the customer. To create graphical visuals based on the data you can integrate Timestream with several visualization toools such as Amazon QuickSight. To learn more about the IoT Core-Timestream rule please see [here](https://docs.aws.amazon.com/iot/latest/developerguide/timestream-rule-action.html).

2. AWS IoT Analytics 
<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-IotAnalytics.png" alt="alt text"/></center>
</br>

In this structure, after capturing the MQTT messages, using IoT Core built in rule, data is sent to an AWS IoT Analytics channel. Then the data will be directed to the Analytics Datastore through the Analytics pipeline. To learn more about the IoT Core to IoT Analytics rule check [here](https://docs.aws.amazon.com/iot/latest/developerguide/iotanalytics-rule-action.html). IoT Analytics automates the steps required to analyze data from IoT devices. It can filter, transform, and enrich IoT data before storing it in a time-series data store for analysis. AWS IoT Analytics is available in the following [regions](https://aws.amazon.com/iot-analytics/pricing/).

3. Amazon Kinesis Data Firehose 

<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-KinesisAthena.png" alt="alt text"/></center>
</br>

In this pattern, the captured MQTT messages in AWS IoT core will be sent to an Amazon Kinesis Data Firehose allowing you to collect, process and analyze large bandwidth of data in real time. The service enables you to author and run code against streaming sources to perform time-series analytics, feed real-time dashboards, and create real-time metrics. You can create a Delivery Stream in the Kinesis Firehose with an S3 bucket as its destination in which the data will be stored. You can then visualize the data in the bucket by building an [Athena table](https://docs.aws.amazon.com/athena/latest/ug/data-sources-glue.html) (using Glue Crawler) on top of that and [connecting Athena to Amazon Quicksight](https://docs.aws.amazon.com/quicksight/latest/user/create-a-data-set-athena.html). Detailed information about the IoT Core rule for sending data to Kinesis Data Firehose is available [here](https://docs.aws.amazon.com/iot/latest/developerguide/kinesis-firehose-rule-action.html). Amazon Kinesis Firehose is available in the following [regions](https://aws.amazon.com/kinesis/data-firehose/pricing/). 

4. Amazon OpenSearch Service
<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-OpenSearch.png" alt="alt text"/></center>
</br>

Amazon OpenSearch Service is a managed service that makes it easy to deploy, operate, and scale OpenSearch clusters in the AWS Cloud. It is a fully open-source search and analytics engine for use cases such as log analytics, real-time application monitoring, and clickstream analysis. To learn more you can refer to [What is Amazon OpenSearch Service?](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/) in the Amazon OpenSearch Service Developer Guide.
In this pattern, the captured data in IoT Core will be pushed to Amazon OpenSearch service through built in IoT rule. You can then use tools like OpenSearch integrated dashboards to query and visualize data in OpenSearch Service. For more details refer to [OpenSearch rule action](https://docs.aws.amazon.com/iot/latest/developerguide/opensearch-rule-action.html).


The subdirectories contain the following: 

* Under `demo` directory, there are the demo templates along with a sample program to run on your Expresslink. 
* Under `aws_cdk` directory, there are the CDK (Cloud Development Kit) stacks used to crate the CloudFormation templates. See [What is the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html) to learn more about AWS CDK.
* Under `user_guides` directory you can find the guides to get started with the templates and how to customize them with AWS CDK. 
