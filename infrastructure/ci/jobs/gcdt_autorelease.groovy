import utilities.InfraUtilities

// this job releases gcdt once a week (Monday 10:00 am)
// can be triggered manually to do the same


environ = InfraUtilities.getEnv()
def branchToCheckout = InfraUtilities.getBranch()
out.println(branchToCheckout)
def slackChannel = InfraUtilities.getSlackChannel()

def credentialsToCheckout = "psd-frontend-jenkins_username-password"
def baseFolder = "infrastructure/ci"
def artifactBucket = "glomex-infra-reposerver-prod"
def releaseScript = baseFolder + "/scripts/release_package.sh"

def packageName = 'gcdt'
def jobName = "glomex-cloud-deployment-tools/" + packageName + "_autorelease"
def repository = "glomex/glomex-cloud-deployment-tools"

folder("glomex-cloud-deployment-tools") {
}


job(jobName) {
    environmentVariables {
        keepSystemVariables(true)
        keepBuildVariables(true)
        env('ENV', environ)
        env('PACKAGE_NAME', packageName)
        env('PYTHONUNBUFFERED', '1')
        env('AWS_DEFAULT_REGION', 'eu-west-1')
        env('BUCKET', artifactBucket + '/pypi/packages/' + packageName + '/')
        // http://chase-seibert.github.io/blog/2014/01/12/python-unicode-console-output.html
        env('PYTHONIOENCODING', 'UTF-8')
    }
    scm {
        git {
            remote {
                github(repository, 'https')
                credentials(credentialsToCheckout)
                branch('master')
            }

            configure { gitScm ->
                gitScm / 'extensions' << 'hudson.plugins.git.extensions.impl.UserExclusion' {
                    excludedUsers('Jenkins Continuous Integration Server')
                }
            }
        }
    }

    triggers {
        cron('H 10 * * 1')
    }

    wrappers {
        preBuildCleanup()
        colorizeOutput()
    }

    steps {
        shell('''
            #git checkout develop
            #git checkout master
            #git merge develop
              '''.stripIndent()
        )

        shell(readFileFromWorkspace(releaseScript))

        // are we done?
        shell("echo 'done done done'")

    }

    publishers {
        git {
            pushOnlyIfSuccess()
            branch('origin', 'master')
            branch('origin', 'develop')
        }
        slackNotifier {
            room(slackChannel)
            notifyAborted(false)
            notifyFailure(true)
            notifyNotBuilt(false)
            notifyUnstable(false)
            notifyBackToNormal(true)
            notifySuccess(false)
            notifyRepeatedFailure(true)
            startNotification(false)
            includeTestSummary(false)
            includeCustomMessage(false)
            customMessage(null)
            buildServerUrl(null)
            sendAs(null)
            commitInfoChoice('NONE')
            teamDomain(null)
            authToken(null)
        }
    }
}
