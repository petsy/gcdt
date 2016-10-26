import utilities.DpUtilities

environ = DpUtilities.getEnv()
def branchToCheckout = DpUtilities.getBranch()
def slackChannel = DpUtilities.getSlackChannel()

out.println(branchToCheckout)

def credentialsToCheckout = "psd-frontend-jenkins_username-password"
//def configFile = readFileFromWorkspace("./operations/continous-delivery/packages-config.json")
//def config = new groovy.json.JsonSlurper().parseText(configFile)
def artifactBucket = "glomex-infra-reposerver-prod"
def buildScript = "infrastructure/ci/scripts/build_python_package.sh"


folder("packages") {

}
def packageName = 'gcdt'
def jobName = "packages/" + packageName
def repository = "glomex/glomex-cloud-deployment-tools"

// this job is setup only on dev!
if (environ != 'dev') {
    return
}

// don't build packages on dev (preprod: develop, prod: master)
//if (environ != "dev") {

//    def defaultBranch = environ == "preprod" ? "develop" : "master"

//    config.jobs.each {

//def packageName = it.name
//def jobName = "packages" + "/" + it.name
//def repository = it.repository

job(jobName) {
    environmentVariables {
        keepSystemVariables(true)
        keepBuildVariables(true)
        env('ENV', environ)
        env('PACKAGE_NAME', packageName)
        env('ARTIFACT_BUCKET', artifactBucket)
        env('PYTHONUNBUFFERED', "1")
    }

    scm {
        git {
            remote {
                github(repository, 'https')
                credentials(credentialsToCheckout)
                branch('$BRANCH')
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
            branch('origin', '$BRANCH')
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

    triggers {
        githubPush()
    }

    wrappers {
        preBuildCleanup()
        colorizeOutput()
    }

    parameters {
        stringParam('BRANCH', defaultValue = defaultBranch)
    }

    steps {

        shell(readFileFromWorkspace(buildScript))

    }
}
