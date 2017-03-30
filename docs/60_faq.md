## Frequently Asked Questions (faq)


### Homebrew Python

If you installed Python via Homebrew on OS X and get this error:

``` bash
must supply either home or prefix/exec-prefix -- not both
```

You can find a solution on [here](http://stackoverflow.com/questions/24257803/distutilsoptionerror-must-supply-either-home-or-prefix-exec-prefix-not-both)


### Environment variables

Be sure to provide the correct environment variables (ENV=PROD/DEV/etc.)


### Using hooks in gcdt

We implemented hooks in gcdt similar to the plugin mechanism.
 
You can use hooks in gcdt in the following places:
 
* use hooks in a `cloudformation.py` template
* use hooks in a `gcdt_<env>.py` config file
* use hooks in a `hookfile.py`. Please specify the location of the `hookfile` in your config file.

For details on gcdt_lifecycle and gcdt_signals please take a look into the gcdt-plugins section of this documentation.
