# Data ingestion and visualization with AWS CloudFormation templates

These CloudFormation templates are prepared to deploy to the cloud and visualize the data coming from your Expresslink. To learn more about AWS CloudFormation, see [**What is CloudFormation?**](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)

These templates are designed in four different patterns to ingest your IoT data using: 

1.  Amazon Timestream
<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-Timstream.png" alt="alt text"/></center>
</br>

2. AWS IoT Analytics 
<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-IotAnalytics.png" alt="alt text"/></center>
</br>

3. Amazon Kinesis Data Firehose 

<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-KinesisAthena.png" alt="alt text"/></center>
</br>

4. Amazon OpenSearch Service
<br>
<center><img src="https://d2908q01vomqb2.cloudfront.net/f6e1126cedebf23e1463aee73f9df08783640400/2022/04/04/Blog-IoT-Reporting-3-OpenSearch.png" alt="alt text"/></center>
</br>

The subdirectories contain the following: 

* Under `demo` directory, there are the demo templates along with a sample program to run on your Expresslink. 
* Under `aws_cdk` directory, there are the CDK (Cloud Development Kit) stacks used to crate the CloudFormation templates. See [What is the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html) to learn more about AWS CDK.
* Under `user_guides` directory you can find the guides to get started with the templates and how to customize them with AWS CDK. 
