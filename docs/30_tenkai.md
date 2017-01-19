## AWS CodeDeploy Tool
### tenkai (展開 from Japanese: deployment)
### Usage

To see available commands, call this:

```bash
	$tenkai
  Usage:
        tenkai deploy
        tenkai version
```

#### deploy
bundles your code then uploads it to S3 as a new revision and triggers a new deployment

#### version
will print the version of gcdt you are using


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
