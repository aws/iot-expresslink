
# Welcome to your CDK project! 
# IoT Data visulaization with Amazon Timestream

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

To specify the same context variable and value in the cdk.json file, use the following sample code.

```
{
  "context": {
    "bucket_name": "mybucket"
  }
}
```

In this project, these are the following parameters to be set: 

* `topic_sql`          
<br>It is required for IoT Core rule creation to add a simplified SQL syntax to filter messages received on an MQTT topic and push the data elsewhere. 
<br> __Format__: Enter an SQL statement using the following: ```SELECT <Attribute> FROM <Topic Filter> WHERE <Condition>```. For example: ```SELECT temperature FROM 'iot/topic' WHERE temperature > 50```. To learn more, see AWS IoT SQL Reference.

* `dimensions`
<br> Each record contains an array of dimensions (minimum 1). Dimensions represent the metadata attributes of a time series data point. Specify the dimension(s) for your data. 
<br> __Format__: Must be in a format of a list of strings. For example, for the input ```[device_id]``` the following key-value would be attached to the IoT Core rule: 
<br>```{dimension's name: device_id, dimension_value: ${device_id}}```</br>

* `timestream_db_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of Timestream databse to hold your data. 
<br> __Format__: Specify a name that is unique for all Timestream databases in your AWS account in the current Region. You can not change this name once you create it. Must be between 3 and 256 characters long. Must contain letters, digits, dashes, periods or underscores.

* `timestream_table_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of Timestream databse to hold your data.  
<br> __Format__: Specify a table name that is unique within its database. You can not change this name once you create it. Must be between 3 and 256 characters long. Must contain letters, digits, dashes, periods or underscores.

* `timestream_iot_rule_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of the IoT Core rule that is going to be created. 
<br> __Format__: Should be an alphanumeric string that can also contain underscore (_) characters, but no spaces.

* `timestream_iot_role_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> An IAM role should be created to grant AWS IoT access to your endpoint. This parameter is for setting the name of this role.
<br> __Format__: Enter a unique role name that contains alphanumeric characters, hyphens, and underscores. A role name can't contain any spaces.

Enjoy!