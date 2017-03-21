## gcdt config reader plugin 

Read config from files in json, python or yaml format.
There is a section called `overview on configuration` above. Please make sure you have that one covered.


### Related documents

* [JSON](https://en.wikipedia.org/wiki/JSON)
* [YAML](https://en.wikipedia.org/wiki/YAML)


### json configuration files

The gcdt_config_reader plugin allows us to have configurations in json format.

The configuration files are environment specific. This means the config file looks like gcdt_<env>.json` where <env> stands for the environment you use (some thing like dev, stage, prod, etc.).


### python configuration files

The gcdt_config_reader plugin allows us to have configurations in python format (with a .py extension).

The configuration files are environment specific. This means the config file looks like gcdt_<env>.py` where <env> stands for the environment you use (some thing like dev, stage, prod, etc.).

The python configuration files have a few specifics which are documented here.

The python configuration only work if they follow the convention to implement a `generate_config()` function. The `generate_config()` needs to return a dictionary with the configuration. Please follow the configuration structure described below.
  
``` python
def generate_config():
    return CFG
```

You can also use hooks in the python config files. Just implement the `register`, `deregister` like they are described in the plugin section to make that work.
