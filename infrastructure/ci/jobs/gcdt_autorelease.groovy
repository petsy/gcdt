import utilities.InfraUtilities

environ = InfraUtilities.getEnv()
def branchToCheckout = InfraUtilities.getBranch()
out.println(branchToCheckout)

def credentialsToCheckout = "psd-frontend-jenkins_username-password"
//def configFile = readFileFromWorkspace("./operations/continous-delivery/packages-config.json")
//def config = new groovy.json.JsonSlurper().parseText(configFile)
def artifactBucket = "glomex-infra-reposerver-prod"

folder("glomex-cloud-deployment-tools") {
}

def packageName = 'gcdt'
def jobName = "glomex-cloud-deployment-tools/" + packageName + "_autorelease"
def repository = "glomex/glomex-cloud-deployment-tools"

// this job is setup only on dev!
if (environ != 'dev') {
    return
}

job(jobName) {
    environmentVariables {
        keepSystemVariables(true)
        keepBuildVariables(true)
        env('ENV', environ)
        env('PACKAGE_NAME', packageName)
        env('PYTHONUNBUFFERED', '1')
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
        // check env
        shell('''
            git checkout develop
            git checkout master
            git merge develop
              '''.stripIndent()
        )

        // are we done?
        shell("echo 'done done done'")

    }

    publishers {
        git {
            pushOnlyIfSuccess()
            branch('origin', 'master')
        }

        downstreamParameterized {
            trigger('gcdt') {
                parameters {
                    // Adds a parameter.
                    predefinedProp('BRANCH', 'master')
                }
            }
        }
    }
}
