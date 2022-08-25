# Getting started with Amazon OpenSearch service template guide 

## Setting up and prerequisites

### AWS Account 

If you don't already have an AWS account follow the [Setup Your Environment](https://aws.amazon.com/getting-started/guides/setup-environment/) getting started guide for a quick overview.

### AWS CloudFormation 

Before you start using AWS CloudFormation, you might need to know what IAM permissions you need, how to start logging AWS CloudFormation API calls, or what endpoints to use. Refer to this [guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/settingup.html) to get started with using AWS CloudFormation.

### AWS  CDK

**Note**: If you are just going to use the sample demo template you can skip this section.

The AWS Cloud Development Kit (CDK) is an open source software development framework that lets you define your cloud infrastructure as code in one of its supported programming languages. It is intended for moderately to highly experienced AWS users. Refer to this [guide](https://aws.amazon.com/getting-started/guides/setup-cdk/?pg=gs&sec=gtkaws) to get started with AWS CDK.

___

## Template deployment and CloudFormation stack creation

A template is a JSON or YAML text file that contains the configuration information about the AWS resources you want to create in the [stack](https://docs.aws.amazon.com/cdk/v2/guide/stacks.html). To learn more about how to work with CloudFormation templates refer to [Working with templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-guide.html) guide. 

You can either use the provided demo template and deploy it directly in the console or customize the template’s resources before deployment using AWS CDK. Based on your decision follow the respective section below. 

### Sample demo template 

By using the sample json template that is provided, you do not need to take any further actions except creating the stack by uploading the template file. For simplicity’s sake, a simple code is provided that you can run on your device. It is an example of multiple devices sending their weather measurements to the cloud through ExpressLink. You can find the code and guide to get it working under `demo/demo_weather_station_code` directory.

Follow the steps below to create the CloudFormation stack using the sample template file. 

1. Sign in to the AWS Management Console and open [AWS CloudFormation console.](https://console.aws.amazon.com/cloudformation)
2. If this is a new CloudFormation account, choose **Create New Stack**. Otherwise, choose **Create Stack** and then select **with new resources**.
3. In the **Template** section, select **Upload a template file** and upload the json template file. Choose **Next**.
4. In the **Specify Details** section, enter a stack name in the **Name** field.
5. If you want you can add tags to your stack. Otherwise choose **Next**.
6. Review the stack’s settings and then choose **Create.**
7. At this point, you will find the status of your stack to be `CREATE_IN_PROGRESS`. Your stack might take several minutes (~15 min) to get created. See next sections to learn about monitoring your stack creation.

### Custom template

If you are interested in using the CloudFormation templates more than just for demo purposes, you probably need to customize the stack’s resources based on your specific use-case. Follow the steps below to do so:

1. Make sure that you already [set up your AWS CDK](https://aws.amazon.com/getting-started/guides/setup-cdk/?pg=gs&sec=gtkaws) environment.
2. Starting in your current directory, change your directory and go to `aws_cdk/OpenSearchPattern` directory.
3. Just to verify everything is working correctly, list the stacks in your app by running `cdk ls` command. If you don't see `OpensearchPatternStack`, make sure you are currently in `OpenSearchPattern` directory.
4. The structure of the files inside `OpenSearchPattern` is as below: 

[Image: Screen Shot 2022-08-25 at 12.52.09 PM.png]
* `open_search_pattern_stack.py`  is the main code of the stack. It is here where the required resources are created. 
* `tests/unit/test_open_search_pattern_stack.py` is where the unit tests of the stack is written. The unit tests check
    * Right creation of the resources in addition to their properties
    * Dependencies between the resources 
    * Right error handlings in case of input violations
* `cdk.json` tells the CDK Toolkit how to execute your app. Context values are key-value pairs that can be associated with an app, stack, or construct. You can add the context key-values to this file or in command line before synthesizing the template.
* `README.md` is where you can find the detailed instructions on how to get started with the code including: how to synthesize the template, a set of useful commands, stack’s context parameters, and details about the code.
* `cdk.out` is where the synthesized template (in a json format) will be located in.

1. Run `source .venv/bin/activate` to activate the app's Python virtual environment.
2. Run `python -m pip install -r requirements.txt` and `python -m pip install -r requirements.txt` to install the dependencies.
3. Go through the `README.md` file to learn about the context parameters that need to be set by you prior to deployment.
4. Set the context parameter values either by changing `cdk.json` file or by using the command line.
    1. To create a command line context variable, use the **`--context (-c) option`**, as shown in the following example: `$ cdk cdk synth -c bucket_name=mybucket+Sheet1!A3`
    2. To specify the same context variable and value in the `cdk.json` file, use the following code.`
          {"context": { "bucket_name": "mybucket"}`
5. Run `cdk synth` to emit the synthesized CloudFormation template.
6. Run `python -m pytest` to run the unit tests. It is the best practice to run the tests before deploying your template to the cloud.
7. Run `cdk deploy` to deploy the stack to your default AWS account/region.
8. Use the instructions in ***Stack management*** section below to manage your stack creation. 

___

## Stack management

### Viewing CloudFormation stack data and resources

After deployment, you may need to monitor your created stack and its resources. To do this, your starting point should be AWS CloudFormation.  

1. Sign in to the AWS Management Console and open [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation).
2. Choose **Stacks** tab to view all the available stacks in your account. 
3. Find the stack that you just created and select it.
4. To verify that the stack’s creation is done successfully, check if its status is `CREATE_COMPLETE`. To learn more about what each status means refer to [stack status codes](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-view-stack-data-resources.html#cfn-console-view-stack-data-resources-status-codes). 
5. You can view the stack information such as its ID, status, policy, rollback configuration, etc under the **Stack info** tab.  
6. If you click on the **Events** tab, each major step in the creation of the stack sorted by the time of each event, with latest events on top is displayed. 
7. You can also find the resources that are part of the stack under the **Resources** tab. 

There is more information about viewing stack information [here](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-view-stack-data-resources.html#cfn-console-view-stack-data-resources-view-info).

###  Monitoring the generated resources

If you deploy and create the stack successfully, the following resources must get created under your stack. You can verify their creation by checking the **Resources** tab in your stack. 

|Resourse	|Type	|
|---	|---	|
|CDKMetadata	|[AWS::CDK::Metadata](https://docs.aws.amazon.com/cdk/api/v1/docs/constructs.ConstructMetadata.html)	|
|Cognito Identity Pool 	|[AWS::Cognito::IdentityPool](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-identitypool.html)	|
|Identity Pool Role Attachment	|[AWS::Cognito::IdentityPoolRoleAttachment](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-identitypoolroleattachment.html)	|
|Cognito User Pool 	|[AWS::Cognito::UserPool](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-userpool.html)	|
|Cognito User Pool Domain	|[AWS::Cognito::UserPoolDomain](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-userpooldomain.html)	|
|IAM role and policy (master user for fine grained access)	|[AWS::IAM::Role](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-role.html) [AWS::IAM::Policy](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-policy.html)	|
|User Pool User creation	|[Custom::AWS](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html)	|
|Cognito User Pool Group	|[AWS::Cognito::UserPoolGroup](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-userpoolgroup.html)	|
|User Pool User/Group Attachment	|[AWS::Cognito::UserPoolUserToGroupAttachment](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-userpoolusertogroupattachment.html)	|
|IAM role and policy that grant OpenSearch access to Cognito	|[AWS::IAM::Role](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-role.html) [AWS::IAM::Policy](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-policy.html)	|
|OpenSearch domain	|[AWS::OpenSearchService::Domain](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-opensearchservice-domain.html)	|
|IoT Rule	|[AWS::IoT::TopicRule](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-topicrule.html)	|
|CloudWatch log group to capture error logs (IoT Core to OpenSearch)	|[AWS::Logs::LogGroup](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-logs-loggroup.html)	|
|IAM role and policy that grant IoT access to the CloudWatch log groups	|[AWS::IAM::Role](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-role.html) [AWS::IAM::Policy](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-policy.html)	|

### Handling stack failures

If CloudFormation fails to create, update, or delete your stack, you will be able to go through the logs or error messages to learn more about the issue. There are some general methods for troubleshooting a CloudFormation failure. For example, you can follow the steps below to find the issue in the console:

* Check the status of your stack in [CloudFormation console](https://console.aws.amazon.com/cloudformation/). 
* From the **Events** tab, you can see a set of events while the last operation was being done on your stack.
* Find the failure event from the set of events and then check the status reason of that event. The status reason usually gives a good understanding of the issue that caused the failure.


In case of failures in stack creations or updates, CloudFormation automatically performs a rollback. However, you can also [add rollback triggers during stack creation or updating](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-rollback-triggers.html#using-cfn-rollback-triggers-create) to further monitor the state of your application. By setting up the rollback triggers if the application breaches the threshold of the alarms you've specified, it will roll back to that operation. 

Finally, this [troubleshooting guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html#basic-ts-guide) is a helpful resource to refer if there is an issue in your stack. 

### Estimating the cost of the stack

There is no additional charge for AWS CloudFormation. You pay for AWS resources created using CloudFormation as if you created them by hand. Refer to this [guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-paying.html) to learn more about the stack cost estimation functionality.

___

## Ingesting and visualizing your IoT data with the constructed resources

### Sending data to the cloud from your device

Now that your stack and all the required resources are created and available, you can start by connecting your device to the cloud and sending your data to the cloud. 

* If you are new to AWS IoT Core, this [guide](https://docs.aws.amazon.com/iot/latest/developerguide/connect-to-iot.html) is a great starting point to connect your device to the cloud. 
* After connecting your device to IoT Core, you can use the [MQTT test client](https://docs.aws.amazon.com/iot/latest/developerguide/view-mqtt-messages.html) to monitor the MQTT messages being passed in your AWS account. 
* Move to the **Rules** tab under **Message Routing** section in [AWS IoT console](https://console.aws.amazon.com/iot/home). There you can verify the creation of the newly created topic rule and its [opensearch rule action](https://docs.aws.amazon.com/iot/latest/developerguide/opensearch-rule-action.html) which writes data from MQTT messages to the Amazon OpenSearch Service domain.

### Access data with OpenSearch Dashboards

* Open [Amazon Opensearch service console](https://console.aws.amazon.com/opensearch).
* From the left navigation pane, choose **Domains.**
* Find the domain that was created by your stack and select it.
* Open the **OpenSearch Dashboards URL** to access the OpenSearch dashboard.  Note that for accessing the OpenSearch dashboards, Cognito authentication is used. (You can find more information about it in [Amazon Cognito authentication for OpenSearch Dashboards](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/cognito-auth.html)). To access the username and password of the master user created by the template for you:
    * If you used the sample template file, use “admin” as username and “Admin123!” as your temporary password. In the first attempt to log in to the dashboard you will be asked to change your temporary password. 
    * If you used the AWS CDK to synthesize the customized template, after running the `cdk deploy` command, you should get a temporary password string that you will use for the first log in to the dashboard. Your username is “admin” by default. However, you can change the username of the master user by modifying `cdk.json` file or using the command line. More details on this can be found in the `README.md` in the stack package. 
    * You should now be successfully logged in to your domain’s OpenSearch dashboard. If there are issues and you cannot log in, check [Troubleshooting](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/handling-errors.html). 
* Before you can use OpenSearch Dashboards, you need an index pattern. Dashboards uses index patterns to narrow your analysis to one or more indices. To match the `iot` index that the template  creates by default, go to **Stack Management > Index Patterns**, and define an index pattern of `iot*`, and then choose **Next step**.
* Now you can start creating visualizations. Choose **Visualize**, and then add a new visualization.

### Optional steps 

* Auto-Tune: Auto-Tune in Amazon OpenSearch Service uses performance and usage metrics from your OpenSearch cluster to suggest memory-related configuration changes, including queue and cache sizes and JVM settings on your nodes which improves cluster speed and stability. See [Auto-Tune for Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/auto-tune.html) fore more details. 

### Integrating with dashboards to visualize data

#### OpenSearch Dashboards

OpenSearch Dashboards is the default visualization tool for data in OpenSearch. Amazon OpenSearch Service provides an installation of OpenSearch Dashboards with every OpenSearch Service domain. Refer to ***Access data with OpenSearch Dashboards*** section above to find more details of how to access the OpenSearch dashboard of your domain. [OpenSearch Dashboards](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/dashboards.html) is a useful document to refer for more details. 

#### Amazon QuickSight

Amazon OpenSearch provides direct integration with [Amazon QuickSight](https://aws.amazon.com/quicksight/). Amazon QuickSight is a fast business analytics service you can use to build visualizations, perform ad-hoc analysis, and quickly get business insights from your data. Amazon QuickSight is available in [these regions](https://docs.aws.amazon.com/general/latest/gr/quicksight.html).

To connect Amazon OpenSearch Service to QuickSight you need to follow these steps: 

1. Navigate to the AWS QuickSight console.
2. If you have never used AWS QuickSight before, you will be asked to sign up. In this case, choose **Standard** tier and your region as your setup.
3. During the sign up phase, give QuickSight access to your Amazon OpenSearch.
4. If you already have an account, give Amazon QuickSight access your OpenSearch by choosing **Admin >** **Manage QuickSight > Security & permissions.** Under QuickSight access to AWS services, choose **Add or remove**, then select the check box next to **OpenSearch** and choose **Update**.
5. From the admin Amazon QuickSight console page choose **New Analysis** and **New data set.**
6. Choose Amazon OpenSearch Service as the source and enter a name for your data source. Choose the connection type you want to use. (If you are using the sample demo template then leave it as **public**) and then choose your domain.
7. Choose **Validate connection** to check that you can successfully connect to OpenSearch Service.
8. Choose **Create data source** to proceed.
9. After your data source is created, you can start making visualizations in Amazon QuickSight.

Refer to [Using Amazon OpenSearch Service with Amazon QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/connecting-to-os.html) for more details on QuickSight integration with OpenSearch. 

___

## Cleaning up the stack

To clean-up all the resources used in this demo, all you need to do is to delete the initial CloudFormation stack. To delete a stack and its resources, follow these steps:

1. Open [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/).
2. On the Stacks page in the CloudFormation console, select the stack that you want to delete. Note that the stack must be currently running.
3. In the stack details pane, choose **Delete**.
4. Confirm deleting stack when prompted. 

After the stack is deleted, the stack’s status will be `DELETE_COMPLETE`. Stacks in the `DELETE_COMPLETE` state aren't displayed in the CloudFormation console by default. However, you can follow the instructions in [viewing deleted stacks on the AWS CloudFormation console](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-view-deleted-stacks.html) to be able to view them. 

Finally, if the stack deletion failed, the stack will be in the `DELETE_FAILED` state. For solutions, see the [Delete stack fails](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html#troubleshooting-errors-delete-stack-fails) troubleshooting topic. In this case, make sure to refer to the **Monitoring the generated resources** section of this document to verify that all the resources got deleted successfully. 

___

## Useful resources 

* [CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/index.html)
* [Amazon OpenSearch User Guide](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/index.html)
* [IoT Core User Guide](https://docs.aws.amazon.com/iot/latest/developerguide/index.html)
* [AWS CDK (v2) User Guide](https://docs.aws.amazon.com/cdk/v2/guide/index.html)
