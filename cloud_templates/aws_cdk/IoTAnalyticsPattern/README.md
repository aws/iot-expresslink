
# Welcome to your CDK project! 
# IoT Data visulaization with AWS IoT Analytics

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
<br>It is required for IoT Core rule creation to add a simplified SQL syntax to filter messages received on an MQTT topic and push the data elsewhere. 
<br> __Format__: Enter an SQL statement using the following: ```SELECT <Attribute> FROM <Topic Filter> WHERE <Condition>```. For example: ```SELECT temperature FROM 'iot/topic' WHERE temperature > 50```. To learn more, see AWS IoT SQL Reference.

* `analytics_channel_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of the IoT Analytics channel that will get connected to the IoT Core to get your data.
<br> __Format__: Choose a unique name that you can easily identify. The channel name must contain 1-128 characters. Valid characters are a-z, A-Z, 0-9, and _ (underscore). 

* `analytics_datastore_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of the IoT Analytics datastore that will get connected to the IoT Core to store your data.  
<br> __Format__: A unique ID identifies your data store. You can't change this ID after you create it. Valid characters: a-z, A-Z, 0-9, and _ (underscore).

* `analytics_dataset_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of the IoT Analytics SQL dataset that will get connected to the IoT Core. A SQL dataset is a materialized view from a data store. 
<br> __Format__: Choose a unique name that you can easily identify. The dataset name must contain 1-128 characters. Valid characters are a-z, A-Z, 0-9, and _ (underscore).

* `analytics_pipeline_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of the IoT Analytics pipeline that will read messages from the channel and write processed data to the datastore.
<br> __Format__: Valid characters: a-z, A-Z, 0-9, and _ (underscore).

* `analytics_iot_rule_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> The name of the IoT Core rule that is going to be created. 
<br> __Format__: Should be an alphanumeric string that can also contain underscore (_) characters, but no spaces.

* `analytics_iot_role_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> An IAM role should be created to grant AWS IoT access to your endpoint. This parameter is for setting the name of this role.
<br> __Format__: Enter a unique role name that contains alphanumeric characters, hyphens, and underscores. A role name can't contain any spaces.

* `channel_storage_type`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> Where channel data is stored. You may choose one of ```serviceManagedS3``` or ```customerManagedS3``` storage. If not specified, the default is ```serviceManagedS3```. This can't be changed after creation of the channel.
<br> __Format__: You should either include ```"channel_storage_type": "service_managed"``` or ```"channel_storage_type": "customer_managed"``` in the cdk.json file or command line. 

* `datastore_storage_type`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> Where data in a data store is stored.. You can choose ```serviceManagedS3``` storage, ```customerManagedS3``` storage, or ```iotSiteWiseMultiLayerStorage``` storage. The default is ```serviceManagedS3```. You can't change the choice of Amazon S3 storage after your data store is created. In this version of the project there is no support for ```iotSiteWiseMultiLayerStorage``` storage. 
<br> __Format__: You should either include ```"datastore_storage_type": "service_managed"``` or ```"datastore_storage_type": "customer_managed"``` in the cdk.json file or command line. 

* `file_format_configuration`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> Contains the configuration information of file formats. IoT Analytics data stores support JSON and Parquet. The default file format is JSON. You can specify only one format and you can't change the file format after you create the data store.
<br> __Format__:  You should either include ```"file_format_configuration": "json"``` or ```"file_format_configuration": "parquet"``` in the cdk.json file or command line. 

* `parquet_file_format_schema_columns`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`
<br> Contains the configuration information of the Parquet format. This parameter is used only if you have set ```file_format_configuration``` to ```"parquet"```.
<br> __Format__:  The input should be a list of dictionaries. Each dictionary represents a single column and should be of the format of ```{"name": name, "type": type}```. 

Enjoy!
