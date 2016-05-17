Glomex Cloud Deployment Tools
===============================

version number: 0.0.2

author: Glomex Data Platform Team

Overview
--------

These tools have emerged from our experiences while working extensively with
Cloudformation, AWS Lambda, API Gateway and CodeDeploy

Installation / Usage
--------------------

Right now there is no central PyPi Repository, so you have to install directly from the file system.


Clone the repo:

    $ git clone https://github.com/GLOMEX/glomex-cloud-deployment-tools.git
    $ python setup.py install


Contributing
------------

If you find any bugs or if you need new features please feel free to issue a pull request with your changes.

Issues and Feature Requests
-------

Please open a GitHub issue for any bug reports and feature requests.

## Common for all Tools
- All tools imply that your working directory is the directory that contains the artifact you want to work with.
- Furthermore you are responsible for supplying a valid set of AWS credentials. A good tool is [aws-mfa](https://pypi.python.org/pypi/aws-mfa/0.0.5)
- Currently you can still supply an ENV parameter to each tool but this is deprecated. In the future you need to set an environment variable "ENV" which indicates the account/staging area you want to work with. This parameter tells the tools which config file to use. Basically something like settings_$(ENV).conf is evaluated in the configuration component.

## Cloudformation Deploy Tool  
### kumo (雲 from Japanese: cloud)

### Usage

To see available commands, call kumo without any arguments:



```bash
$kumo
Usage:
        kumo deploy [-e ENV]
        kumo list
        kumo delete -f [-e ENV]
        kumo generate [-e ENV]
        kumo validate [-e ENV]
        kumo scaffold [<stackname>]
        kumo configure
        kumo preview
```

### Commands

#### deploy
will create or update a CloudFormation stack

#### list
will list all available CloudFormation stacks

#### delete
will delete a CloudFormation stack

#### generate
will generate the CloudFormation template for the given stack and write it to your current working directory.

#### validate
will validate your CloudFormation template. Warning: deploys can still fail

#### scaffold
create a new CloudFormation stack in your current working directory from a CookieCutter template

#### configure
you need to run this on first run

#### preview
will create a CloudFormation ChangeSet with your current changes to the template

### Folder Layout

The folder layout looks like this:


cloudformation.py -> creates troposphere template, needs a method like this:

``` python
def generate_template():
    return t.to_json()
```

settings_dev.conf -> settings for dev in [hocon](https://github.com/typesafehub/config/blob/master/HOCON.md) format, needs to include all parameters for the cloudformation template + stack name

settings_prod.conf -> settings for prod in [hocon](https://github.com/typesafehub/config/blob/master/HOCON.md) format, needs to include all parameters for the cloudformation template + stack name

#### Config file example

```json
cloudformation {
  StackName = "sample-stack"

}
```

You can create a new folder with this structure by calling `kumo scaffold`.

### Howto
1. create a new local folder from the template: `kumo scaffold`
2. fill `cloudformation.py`with the contents of your stack
3. fill `settings_ENV.conf`with valid parameters for your CloudFormation template
4. call `kumo validate`to check your template for errors
5. call `kumo deploy`to deploy your stack to AWS


## API Gateway Deploy Tool
### yugen (幽玄 from Japanese: “dim”, “deep” or “mysterious”)

### Usage

To see available commands, call this:
```bash
	$yugen
  Usage:
        yugen deploy [--env=<env>]
        yugen delete -f [--env=<env>]
        yugen export
        yugen list
        yugen apikey-create <keyname>
        yugen apikey-list
        yugen apikey-delete
```

#### deploy
creates/updates an API from a given swagger file

#### export
exports the API definition to a swagger file

#### list
lists all existing APIs

#### apikey-create
creates an API key

#### apikey-list
lists all existing API keys

#### apikey-delete
deletes an API key

### Folder Layout

swagger.yaml -> API definition in swagger with API Gateway extensions

api.conf -> settings for the API which is needed for wiring

```
api {
    name = "dp-dev-serve-api-2"
    description = "description"
    targetStage = "dev"
    apiKey = "xxx"
}

lambda {

    entries = [
      {
        name = "dp-dev-serve-api-query"
        alias = "ACTIVE"
      },
      {
        name = "dp-dev-serve-api-query-elasticsearch"
        alias = "ACTIVE"
      }
    ]
    
}
```


## AWS Lambda Deploy Tool
### ramuda (ラムダ from Japanese: lambda)

### Usage

To see available commands, call this:

```bash
	$ramuda
  Usage:
        ramuda bundle [--env=<env>]
        ramuda deploy [--env=<env>]
        ramuda list
        ramuda metrics <lambda>
        ramuda wire [--env=<env>]
        ramuda unwire [--env=<env>]
        ramuda delete -f <lambda>
        ramuda rollback <lambda> [<version>]
```

#### bundle
zips all the files belonging to your lambda according to your config and requirements.txt and puts it in your current working directory as `bundle.zip`. Useful for debugging as you can still provide different environments.

#### deploy
deploys a lambda function to AWS. If the lambda function is non-existent it will create a new one. For an existing lambda function it checks whether code has changed and updates accordingly. In any case configuration will be updated and an alias called "ACTIVE" will be set to this version.

#### list
lists all existing lambda functions including additional information like config and active version:
```bash
dp-dev-store-redshift-create-cdn-tables
	Memory: 128
	Timeout: 180
	Role: arn:aws:iam::644239850139:role/lambda/dp-dev-store-redshift-cdn-LambdaCdnRedshiftTableCr-G7ME657RXFDB
	Current Version: $LATEST
	Last Modified: 2016-04-26T18:03:44.705+0000
	CodeSha256: KY0Xk+g/Gt69V0siRhgaG7zWbg234dmb2hoz0NHIa3A=
```

#### metrics
displays metric for a given lambda:
```bash
dp-dev-ingest-lambda-cdnnorm
	Duration 488872443
	Errors 642
	Invocations 5202
	Throttles 13
```

#### wire
"wires" the lambda function to its event configuration. This actually activates the lambda function.

#### unwire
delets the event configuration for the lambda function

#### delete
deletes a lambda function

#### rollback
sets the active version to ACTIVE -1 or to a given version


### Folder Layout

lambda_ENV.conf -> settings for Lambda function

```json
lambda {
  name = "dp-dev-store-redshift-load"
  description = "Lambda function which loads normalized files into redshift"
  role = "arn:aws:iam::644239850139:role/lambda/dp-dev-store-redshift-cdn-lo-LambdaCdnRedshiftLoad-DD2S84CZFGT4"

  handlerFunction = "handler.lambda_handler"
  handlerFile = "handler.py"
  timeout = "180"
  memorySize = "128"
  events {
    s3Sources = [
        { bucket = "dp-dev-store-cdn-redshift-manifests", type = "s3:ObjectCreated:*", suffix = ".json" }
    ]
  }
  vpc  {
    subnetIds = ["subnet-87685dde", "subnet-9f39ccfb", "subnet-166d7061"]
    securityGroups = ["sg-ae6850ca"]
  }
}

bundling {
  zip = "bundle.zip"
  folders = [
    { source = "../redshiftcdnloader", target = "./redshiftcdnloader"}
    { source = "psycopg2-linux", target = "psycopg2" }
  ]
}

deployment {
  region = "eu-west-1"
}

```

settings_env.conf -> settings for your code



## AWS CodeDeploy Tool
### tenkai (展開 from Japanese: deployment)
### Usage

To see available commands, call this:

```bash
	$tenkai
  Usage:
        tenkai deploy [-e ENV]

```


#### deploy
bundles your code then uploads it to S3 as a new revision and triggers a new deployment



### Folder Layout

codedeploy -> folder containing your deployment bundle

codedeploy_env.conf -> settings for your code
```json
codedeploy {
applicationName = "mep-dev-cms-stack2-mediaExchangeCms-F5PZ6BM2TI8",
deploymentGroupName = "mep-dev-cms-stack2-mediaExchangeCmsDg-1S2MHZ0NEB5MN",
deploymentConfigName = "CodeDeployDefaultemplate.AllAtOnce01"
artifactsBucket = "7finity-portal-dev-deployment"
}
```


## General advice
### Homebrew Python

If you installed Python via Homebrew on OS X and get this error:

"must supply either home or prefix/exec-prefix -- not both"

You can find a solution here:

http://stackoverflow.com/questions/24257803/distutilsoptionerror-must-supply-either-home-or-prefix-exec-prefix-not-both
### Environment variables
Be sure to provide the correct environment variables (ENV=PROD/DEV/etc.)
