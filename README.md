Glomex Cloud Deployment Tools
===============================

version number: 0.0.1

author: Glomex Data Platform Team

Overview
--------

These tools have emerged from our experiences while working extensively with
Cloudformation, AWS Lambda and API Gateway

Installation / Usage
--------------------

Clone the repo:

    $ git clone https://github.com/GLOMEX/glomex-cloud-deployment-tools.git
    $ python setup.py install

Contributing
------------

TBD

Example
-------

TBD


## Cloudformation Deploy Tool

### Usage

To see available commands, call this:

	$kumo

### Migration / Folder Layout

New layout looks like this:


cloudformation.py -> creates troposphere template, needs a method like this:

```
def generate_template():
    return t.to_json()
```

settings_dev.conf -> settings for dev in hocon format, needs to include all parameters for the cloudformation template + stack name

settings_prod.conf -> settings for prod in hocon format, needs to include all parameters for the cloudformation template + stack name


## API Gateway  Deploy Tool

### Usage

To see available commands, call this:

	$ yugen


### Folder Layout

swagger.yaml -> API definition in swagger wit API Gateway extensions

api.conf -> settings for the API which is needed for wiring


## AWS Lambda Deploy Tool

### Usage

To see available commands, call this:

	$ ramuda

### Folder Layout

lambda_ENV.conf -> settings for Lambda function

settings_env.conf -> settings for your code

## General advice

If you installed Python via Homebrew on OS X and get this error:

"must supply either home or prefix/exec-prefix -- not both"

You can find a solution here:

http://stackoverflow.com/questions/24257803/distutilsoptionerror-must-supply-either-home-or-prefix-exec-prefix-not-both
