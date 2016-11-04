import utilities.InfraUtilities

// if a pull request is merged into develop this job bumps the dev level version
// and releases a dev version to PyPi for testing

environ = InfraUtilities.getEnv()
def branchToCheckout = InfraUtilities.getBranch()
//def slackChannel = InfraUtilities.getSlackChannel()

out.println(branchToCheckout)

def credentialsToCheckout = "glomex-ops-deploy_username_password"
def baseFolder = "infrastructure/ci"
def artifactBucket = "glomex-infra-reposerver-prod"
//def venvScript = baseFolder + "/scripts/prepare_virtualenv.sh"
def buildScript = baseFolder + "/scripts/build_develop.sh"

def packageName = 'gcdt-bump-dev-level'
def jobName = "glomex-cloud-deployment-tools/" + packageName
def repository = "glomex/glomex-cloud-deployment-tools"
//def defaultBranch = "develop"  // the BRANCH config could be simplified

folder("glomex-cloud-deployment-tools") {
}


job(jobName) {
    environmentVariables {
        keepSystemVariables(true)
        keepBuildVariables(true)
        env('ENV', environ)
        env('PACKAGE_NAME', packageName)
        env('ARTIFACT_BUCKET', artifactBucket)
        env('PYTHONUNBUFFERED', "1")
        env('AWS_DEFAULT_REGION', 'eu-west-1')
        // http://chase-seibert.github.io/blog/2014/01/12/python-unicode-console-output.html
        env('PYTHONIOENCODING', 'UTF-8')
    }

    scm {
        git {
            remote {
                github(repository, 'https')
                credentials(credentialsToCheckout)
                //branch('$BRANCH')
                branch('develop')
            }

            configure { gitScm ->
                gitScm / 'extensions' << 'hudson.plugins.git.extensions.impl.UserExclusion' {
                    excludedUsers('Jenkins Continuous Integration Server')
                }
            }
        }
    }

    publishers {
        git {
            pushOnlyIfSuccess()
            //branch('origin', '$BRANCH')
            branch('origin', 'develop')
        }
    }

    triggers {
        githubPush()
    }

    wrappers {
        preBuildCleanup()
        colorizeOutput()
    }

    //parameters {
    //    stringParam('BRANCH', defaultValue = defaultBranch)
    //}

    steps {
        //shell(readFileFromWorkspace(venvScript))

        shell(readFileFromWorkspace(buildScript))
    }
}
