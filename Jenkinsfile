#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library@release/2.1.0']) _

def projectConfig

pipeline {
    agent any

    environment {
        sqa_config_docs = ".sqa/config-docs.yml"
        // set the tag, if "master" => based on the py package version, otherwise "BRANCH_NAME"
        PY_PACKAGE_VERSION = sh (returnStdout: true, script: 'python3 ./setup.py --version').trim()
        O3API_DOCKER_TAG = "${env.BRANCH_NAME == 'master' ? env.PY_PACKAGE_VERSION : env.BRANCH_NAME}"      
        // get the current date
        O3API_UPDATE_DATE = sh (returnStdout: true, script: 'date +%y%m%d_%H%M%S').trim()
    }

    stages {
        stage('SQA baseline dynamic stages') {
            // Run the pipeline only if the source code is updated
            when {
                anyOf {
                   changeset 'docker/*'
                   changeset 'o3api/*'
                   changeset '*requirements.txt'
                   changeset 'Jenkinsfile'
                   triggeredBy 'TimerTrigger'
                   triggeredBy cause: 'UserIdCause'
                }
            }
            steps {
                sleep(time:12,unit:"SECONDS")
                script {
                    // update config.yml for Jenkins_ID
                    //sh "bash .sqa/update-config-yml"
                    echo env.O3API_DOCKER_TAG
                    echo env.O3API_UPDATE_DATE
                    projectConfig = pipelineConfig()
                    buildStages(projectConfig)
                }
            }
            post {
                cleanup {
                    cleanWs()
                }
            }
        }
        stage('SQA Documentation') {
            // Run the stage if the documentation or source code are updated
            when {
                anyOf {
                   changeset 'docs/*'
                   changeset 'o3api/*'
                   changeset '*requirements.txt'
                   changeset 'Jenkinsfile'
                   triggeredBy 'TimerTrigger'
                   triggeredBy cause: 'UserIdCause'
                }
            }
            steps {
                script {
                    projectConfig = pipelineConfig(configFile: env.sqa_config_docs)
                    buildStages(projectConfig)
                }
            }
            post {
                cleanup {
                    cleanWs()
                }
            }
        }
        
        // Trigger another job (o3k8s) for Service Deployment Testing
        stage("SvcQA") {
            when {
                anyOf {
                   changeset 'docker/*'
                   changeset 'o3api/*'
                   changeset '*requirements.txt'
                   changeset 'Jenkinsfile'
                   triggeredBy 'TimerTrigger'
                   triggeredBy cause: 'UserIdCause'
                }
            }
            steps {
                script {
                    def svcqa_result = build job: 'eosc-synergy-org/o3k8s/main', parameters: [], propagate: true, wait: true
                    svcqa_result_url = svcqa_result.absoluteUrl
                }
            }
        }
    }
}
