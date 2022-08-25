
# Welcome to your CDK project! 
# IoT Data visulaization with Amazon Opensearch Service 

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

* `opensearch_domain_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
The name of the Opensearch domain that will be created.
<br> __Format__: The name must start with a lowercase letter and must be between 3 and 28 characters. Valid characters are a-z (lowercase only), 0-9, and - (hyphen).

* `opensearch_index_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
Before you can search data, you must index it. Indexing is the method by which search engines organize data for fast retrieval. The resulting structure is called, fittingly, an index. The name of the index that the IoT Core will use to send data to Opensearch is set via this parameter.
<br> __Format__: OpenSearch Service indexes have the following naming restrictions:

    * All letters must be lowercase.

    * Index names cannot begin with `_` or `-`.

    * Index names can't contain `spaces, commas, :, ", *, +, /, \, |, ?, #, >, or <`.

* `opensearch_type_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
It resresents the type of the document that is going to be put under the index. Take the following example: <br>``` {
        "_index" : "movies",
        "_type" : "_doc",
        "_id" : "1",
        "_score" : 0.2876821,
        "_source" : {
          "director" : "Burton, Tim",
          "genre" : [
            "Comedy",
            "Sci-Fi"
          ],
          "year" : 1996,
          "actor" : [
            "Jack Nicholson",
            "Pierce Brosnan",
            "Sarah Jessica Parker"
          ],
          "title" : "Mars Attacks!"
        }```

* `cognito_user_pool_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
During the user pool creation process, you must specify a user pool name. This name can't be changed after the user pool has been created.
<br> __Format__: User pool names must be between one and 128 characters long. They can contain uppercase and lowercase letters (a-z, A-Z), numbers (0-9), and the following special characters: + = , . @ and -.

* `cognito_user_pool_domain_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
The domain name for the domain that hosts the sign-up and sign-in pages for your application.
<br> __Format__: This string can include only lowercase letters, numbers, and hyphens. Don't use a hyphen for the first or last character. Use periods to separate subdomain names. It must be between 1 and 63 characters.

* `cognito_identity_pool_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
Identity pools are used to store end user identities. To declare a new identity pool, you should provide a unique name.
<br> __Format__: It must be between 1 and 128 characters and follow such pattern: ```[\w\s+=,.@-]+ ```

* `cognito_user_username`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
 Each user has a username attribute. Amazon Cognito automatically generates a user name for federated users. You must provide a username attribute to create a native user in the Amazon Cognito directory. After you create a user, you can't change the value of the username attribute.

 * `iot_to_opensearch_rule_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
The name of the IoT Core rule that is going to be created. 
<br> __Format__: Should be an alphanumeric string that can also contain underscore (_) characters, but no spaces

 * `iot_to_opensearch_role_name`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
An IAM role should be created to grant AWS IoT access to Opensearch. This parameter is for setting the name of this role.
<br> __Format__: Enter a unique role name that contains alphanumeric characters, hyphens, and underscores. A role name can't contain any spaces.

 * `opensearch_domain_capacity_config`&nbsp;&nbsp;&nbsp;&nbsp;`<Optional>`      
Configures the capacity of the cluster such as the instance type and the number of instances.
<br> __Format__: Your input must be in the following format:
<br> 

``` 
# Do not include "opensearch_domain_master_nodes" and "opensearch_domain_warm_nodes" keys if you do not want them in your cluster's config.
{ 
  "opensearch_domain_data_nodes":  <int>, 
  "opensearch_domain_data_node_instance_type": <string>, 
  "opensearch_domain_master_nodes":  <int>,   
  "opensearch_domain_warm_nodes":  <int>    
} 
``` 

Enjoy!
