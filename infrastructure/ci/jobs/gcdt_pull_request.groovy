import utilities.DpUtilities

environ = DpUtilities.getEnv()
def branchToCheckout = DpUtilities.getBranch()
def slackChannel = DpUtilities.getSlackChannel()

out.println(branchToCheckout)

// TODO
def credentialsToCheckout = "psd-frontend-jenkins_username-password"
//def configFile = readFileFromWorkspace("./operations/continous-delivery/packages-config.json")
//def config = new groovy.json.JsonSlurper().parseText(configFile)
def baseFolder = "infrastructure/ci"
def artifactBucket = "glomex-infra-reposerver-prod"
def venvScript = baseFolder + "/scripts/prepare_virtualenv.sh"
def buildScript = baseFolder + "/scripts/build_package.sh"
def lifecycleScript = baseFolder + "/scripts/gcdt_lifecycle.sh"


folder("packages") {

}

def packageName = 'gcdt'
def jobName = "glomex cloud deployment tools/" + packageName + "_pull_request"
def repository = "glomex/glomex-cloud-deployment-tools"

// this job is setup only on dev!
//if (environ != 'dev') {
//    return
//}

job(jobName) {
    environmentVariables {
        keepSystemVariables(true)
        keepBuildVariables(true)
        env('ENV', environ)
        env('PACKAGE_NAME', packageName)
        env('ARTIFACT_BUCKET', artifactBucket)
        env('PYTHONUNBUFFERED', '1')
        env('BRANCH', 'develop')
        // http://chase-seibert.github.io/blog/2014/01/12/python-unicode-console-output.html
        env('PYTHONIOENCODING', 'UTF-8')
        // vars specific to gcdt
        env('ACCOUNT', 'dp')
        env('AWS_DEFAULT_REGION', 'eu-west-1')
        env('BUCKET', artifactBucket + '/pypi/packages/' + packageName + '/')
    }
    scm {
        git {
            remote {
                github(repository, 'https')
                credentials(credentialsToCheckout)
                branch('${sha1}')
                refspec('+refs/pull/*:refs/remotes/origin/pr/*')
            }
            configure { gitScm ->
                gitScm / 'extensions' << 'hudson.plugins.git.extensions.impl.UserExclusion' {
                    excludedUsers('Jenkins Continuous Integration Server')
                }
            }
        }
    }

    throttleConcurrentBuilds {
        maxTotal(1)
    }

    /* I do not think we need publishers for pull requests
    publishers {
    }*/

    triggers {
        githubPullRequest {
            orgWhitelist(['glomex'])  // ma_github_org
            cron('H/5 * * * *')
            onlyTriggerPhrase(false)
            useGitHubHooks(false)
            permitAll()

            autoCloseFailedPullRequests(false)
            allowMembersOfWhitelistedOrgsAsAdmin(false)
            // whitelist target branch is missing in the config??
            extensions {
                commitStatus {
                    //context('deploy to staging site')
                    //triggeredStatus('starting deployment to staging site...')
                    //startedStatus('deploying to staging site...')
                    //statusUrl('http://mystatussite.com/prs')
                    completedStatus('SUCCESS', 'All is well')
                    completedStatus('FAILURE', 'Something went wrong.')
                    completedStatus('PENDING', 'processing...')
                    completedStatus('ERROR', 'Something went wrong!')
                }
            }
        }
    }

    wrappers {
        preBuildCleanup()
        colorizeOutput()

        credentialsBinding {
            usernamePassword('GIT_CREDENTIALS', 'psd-frontend-jenkins_username-password')
        }
    }

    //parameters {
    //    stringParam('BRANCH', defaultValue = "develop")
    //}

    steps {
        // check env
        shell('''
            echo $ghprbPullId
            if [ -v $ghprbPullId ]
            then
                echo "not inside a pull request - bailing out!"
                exit 1
            fi
              '''.stripIndent())

        // prepare virtualenv
        shell(readFileFromWorkspace(venvScript))

        // run the unit tests
        // shell('./venv/bin/nosetests --with-coverage --cover-erase --cover-package=gcdt tests/test_*')
        shell('./venv/bin/python -m pytest --cov gcdt tests/test_*')

        // run the style checks
        shell('./venv/bin/pylint gcdt || true')

        // build the package and publish to repo server
        shell(readFileFromWorkspace(buildScript))

        // run the gcdt lifecycle 
        shell(readFileFromWorkspace(lifecycleScript))

        // are we done?
        shell("echo 'done done done'")
    }
}
