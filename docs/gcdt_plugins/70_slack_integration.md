## slack integration plugin

Announce the status of your deployments on slack.


### Related documents

* [Python requests library](http://docs.python-requests.org/en/master/)
* [Slack webhooks](https://api.slack.com/incoming-webhooks)
* [Test tool for requests library](https://github.com/bhodorog/pytest-vts)


### slack integration plugin functionality

Announce deployments on the slack channel for your squad: 

![slack integration](/_static/images/slack_notifications.png "slack integration")

In case a deployments fails you get a notification, too: 

![slack integration](/_static/images/slack_notification_failed.png "slack integration")


### Setup

To setup the slack integration for your account you need two things:

* a [slack webhook](https://api.slack.com/incoming-webhooks)
* you need to add the slack webhook to credstash so the `lookup:secret` works


Add a secret to credstash as follows (maybe check for an existing key first):

``` bash
credstash put datadog_api_key <my_key>
```


### Configuration

`datadog.api_key` is provided via secret lookup:

``` js
    ...
    'plugins': {
        'slack_integration': {
            'channel': '<my_squad_slack_channel>'
        },
        ...
    }
```

Note the `slack_webhook` configuration is provided via default configuration. You do not need to change that as long as you are happy with the default config:

``` js
            'slack_webhook': 'lookup:secret:slack.webhook:CONTINUE_IF_NOT_FOUND'
```
