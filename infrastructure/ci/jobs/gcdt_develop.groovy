import utilities.InfraUtilities

// if a pull request is merged into develop this job bumps the dev level version
// and releases a dev version to PyPi for testing

environ = InfraUtilities.getEnv()
def branchToCheckout = InfraUtilities.getBranch()

out.println(branchToCheckout)

def credentialsToCheckout = "psd-frontend-jenkins_username-password"
def baseFolder = "infrastructure/ci"
def artifactBucket = "glomex-infra-reposerver-prod"
def buildScript = baseFolder + "/scripts/build_develop.sh"

def packageName = 'gcdt'
def jobName = "glomex-cloud-deployment-tools/" + packageName + "-bump-patch-level"
def repository = "glomex/glomex-cloud-deployment-tools"

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
        env('BUCKET', artifactBucket + '/pypi/packages/' + packageName + '/')
    }

    parameters {
        labelParam('NODE') {
            defaultValue('infra-dev')
        }
    }

    scm {
        git {
            remote {
                github(repository, 'https')
                credentials(credentialsToCheckout)
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
            branch('origin', 'develop')
        }
    }

    /*triggers {
        //githubPush()
        scm('H/5 * * * *')
    }*/

    wrappers {
        preBuildCleanup()
        colorizeOutput()
    }

    steps {
        shell(readFileFromWorkspace(buildScript))
    }
}
