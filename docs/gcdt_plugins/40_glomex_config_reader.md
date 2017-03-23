## glomex config reader plugin 

`glomex_config_reader` implements reading classic gcdt hocon config files for all gcdt tools. It also implements the deprecated hook formats for kumo and ramuda.


### Related documents

* [hocon config format](https://github.com/typesafehub/config)
* [hocon in python](https://github.com/chimpler/pyhocon)


### config reader features

* read hocon config from files
* read the many different config files all gcdt tools


### command conf2json

The new features like gcdt scaffolding work with the json config format. So if you want to convert your configuration from hocon to json format you can use the `conf2json` command. This is meant to be a one-off which means to convert the hocon config once and then further maintain the configuration in json format. 
`conf2json` is very well tested since we used it to convert all configurations in gcdt tests to json format.

`conf2json` provides the following functionality:

* convert configuration to json format
* work on one folder
* find out which environments are configured
* iterate over configured environments
* read all config files for one environment
* save gcdt configuration in json format gcdt_<env>.json
