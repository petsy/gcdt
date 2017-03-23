## Installing gcdt

gcdt installation comes in two flavours


### What you need to know about python package management

TODO


### Maintaining dependencies for your project

It is a very common practice not to install Python packages by hand. Instead dependencies and version are managed in a documented and repeatable way. Basically you add the names and versions of your packages to a text file. Most projects also group their dependencies into `direct` dependencies of the service or application and packages they need to develop, build, test and document.

The grouping is not enforced by packaging but to have a std. within an organization is beneficial especially if your want to reuse CI/CD tools.

A little opinionated but pretty common:

* `requirements.txt` tools and packages your service directly depends on
* `requirements_dev.txt` tools and packages you need to develop and test your service
* `requirements_docs.txt` tools you need to write and build your documentation

TODO document version schema

* add gcdt to your requirements_dev.txt
* add the plugins you use to requirements_dev.txt


### Installation (advanced mode / hacker mode)

#### Setup virtualenv

Using virtualenv is a little bit evolved so some people do not like to use it. There is three things you need to do.

* create a virtualenv ('$ virtualenv venv')
* install the packages you want to use (see below)
* a virtualenv works basically like every other technical device, you need to switch it on before you can use it ('$ source ./venv/bin/activate')


TODO add private repo deps

All gcdt packages live in a private PyPi repository. See [reposerver](http://reposerver-prod-eu-west-1.infra.glomex.cloud/pypi/) for instructions.


#### Install your dependencies

``` bash
$ pip install -r requirements.txt -r requirements_dev.txt
```

If you have additional docs - dependencies for your project you need to install them, too:

``` bash
$ pip install -r requirements_docs.txt
```


#### Activate a virtualenv before use

Again make sure you activate a virtualenv before you can use it:

``` bash
$ source ./venv/bin/activate
```


#### Deactivate a virtualenv

I do not throw away my lawn mower once I am done but with my terminals I do that. But you can deactivate a virtualenv:

``` bash
$ deactivate
```


### Use the gcdt installer (simple mode)

TODO

