## glomex lookups plugin

The lookups functionality was previously part of the hocon config reader. The lookup functionality was refactored into this `glomex_lookups` plugin and with the refactoring we also pinned the functionality it into a dedicated lifecycle step. 


### Related documents

* [glomex credstash](https://github.com/glomex/glomex-credstash)


### lookup stack output

The `stack` lookup is used to substitute configuration where the value is an output from another cloudformation stack.

format: `lookup:stack:<stackname>:<output>`
sample: `lookup:secret:slack.token`


### lookup ssl certificate

format: `lookup:ssl:<stackname>:<output>`
sample: `lookup:ssl:wildcard.glomex.com`

'ssl' is configured as lookup by default so for each stack also the certificates are added to stackdata.


### lookup secret

The `secret` lookup is used to substitute configuration where the value is a password, token or other sensitive information that you can not commit to a repository.  
 
format: `lookup:secret:<name>.<subname>`
sample: `lookup:secret:datadog_api_key`
lookup the 'datadog_api_key' entry from credstash
sample: `lookup:secret:slack.webhook:CONTINUE_IF_NOT_FOUND`
lookup the 'slack.token' entry from credstash

note that the `slack.token` lookup does not fail it the accounts credstash does not have the `slack.token` entry.


### lookup baseami

The `baseami` lookup is used lookup the baseami for cloudformation infrastructures.
