
# Welcome to your CDK project! 
# IoT Data visulaization with Amazon Kinesis

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## Context parameters 
There are multiple context parameters that you need to set before synthesizing or delpoying this CDK stack. You can specify a context variable either as part of an AWS CDK CLI command, or in `cdk.json`.
To create a command line context variable, use the __--context (-c) option__, as shown in the following example.

```
$ cdk cdk synth -c bucket_name=mybucket
```

To specify the same context variable and value in the cdk.json file, use the following code.

```
{
  "context": {
    "bucket_name": "mybucket"
  }
}
```

In this project, these are the following parameters to be set: 

* `topic_sql`          
It is required for IoT Core rule creation to add a simplified SQL syntax to filter messages received on an MQTT topic and push the data elsewhere. 
<br> __Format__: Enter an SQL statement using the following: ```SELECT <Attribute> FROM <Topic Filter> WHERE <Condition>```. For example: ```SELECT temperature FROM 'iot/topic' WHERE temperature > 50```. To learn more, see AWS IoT SQL Reference.

* `kinesis_destination_bucket_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
To specify the destination settings for your delivery stream, a s3 bucket must be created and this parameter is for setting the name of it.
<br> __Format__: Bucket name must be unique and must not contain spaces or uppercase letters. [See rules for bucket naming](https://docs.aws.amazon.com/console/s3/bucket-naming) 

* `kinesis_delivery_stream_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
The name of the Kinesis delivery stream to get your data and send them to the s3 bucket.  
<br> __Format__: Acceptable characters are uppercase and lowercase letters, numbers, underscores, hyphens, and periods.

* `kinesis_delivery_stream_role_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
An IAM role should be created to grant Firehose access to your s3 bucket. This parameter is for setting the name of this role.
<br> __Format__: Enter a unique role name that contains alphanumeric characters, hyphens, and underscores. A role name can't contain any spaces.

* `kinesis_iot_rule_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
The name of the IoT Core rule that is going to be created. 
<br> __Format__: Should be an alphanumeric string that can also contain underscore (_) characters, but no spaces.

* `kinesis_iot_role_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
An IAM role should be created to grant AWS IoT access to your endpoint. This parameter is for setting the name of this role.
<br> __Format__: Enter a unique role name that contains alphanumeric characters, hyphens, and underscores. A role name can't contain any spaces.

* `glue_crawler_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
 A Glue crawler should be created to crawl the data in your s3 bucket. This parameter is for setting the name of this cralwer.

* `glue_db_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
A Glue database should be created to connect to the crawler and store data. This parameter is for setting the name of this database.

* `glue_crawler_role_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
An IAM role should be created to grant Glue access to your s3 bucket. This parameter is for setting the name of this role.
<br> __Format__: Enter a unique role name that contains alphanumeric characters, hyphens, and underscores. A role name can't contain any spaces.

Enjoy!
