#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library@1.2.3']) _

def job_result_url = ''

pipeline {
    agent {
        label 'python3.6'
    }

    environment {
        author_name = "Tobias Kerzenmacher (IMK)"
        author_email = "tobias.kerzenmacher@kit.edu"
        app_name = "o3as"
        dockerhub_repo = "synergyimk/o3as"
    }

    stages {
        stage('Code fetching') {
            steps {
                checkout scm
            }
        }

        stage('Style analysis: PEP8') {
            steps {
                ToxEnvRun('pep8')
            }
            post {
                always {
                    // TODO: migrate to new "warnings-ng-plugin"
                    // [!] "warnings" reached end-of-life
                    warnings canComputeNew: false,
                             canResolveRelativePaths: false,
                             defaultEncoding: '',
                             excludePattern: '',
                             healthy: '',
                             includePattern: '',
                             messagesPattern: '',
                             parserConfigurations: [[parserName: 'PYLint', pattern: '**/flake8.log']],
                             unHealthy: ''
                }
            }
        }

        stage('Unit testing coverage') {
            steps {
                ToxEnvRun('cover')
                ToxEnvRun('cobertura')
            }
            post {
                success {
                    HTMLReport('cover', 'index.html', 'coverage.py report')
                    CoberturaReport('**/coverage.xml')
                }
            }
        }

        stage('Metrics gathering') {
            agent {
                label 'sloc'
            }
            steps {
                checkout scm
                SLOCRun()
            }
            post {
                success {
                    SLOCPublish()
                }
            }
        }

        stage('Security scanner') {
            steps {
                ToxEnvRun('bandit-report')
                script {
                    if (currentBuild.result == 'FAILURE') {
                        currentBuild.result = 'UNSTABLE'
                    }
               }
            }
            post {
               always {
                    HTMLReport("/tmp/bandit", 'index.html', 'Bandit report')
                }
            }
        }

        stage('Docker image building') {
            when {
                anyOf {
                    branch 'master'
                    branch 'test'
                    buildingTag()
                }
            }
            steps{
                cleanWs()
                checkout scm
                script {
                    // build different tags
                    id = "${env.dockerhub_repo}"

                    if (env.BRANCH_NAME == 'master') {
                       // debian (aka default)
                       id_deb = DockerBuild(id,
                                            tag: ['latest', 'debian'], 
                                            build_args: ["base=debian",
                                                         "tag=stable-slim",
                                                         "branch=master"])
                    }

                    if (env.BRANCH_NAME == 'test') {
                       // debian (aka default)
                       id_deb = DockerBuild(id,
                                            tag: ['test', 'debian-test'], 
                                            build_args: ["base=debian",
                                                         "tag=stable-slim",
                                                         "branch=test"])
                       // ubuntu
                       //id_ubuntu = DockerBuild(id,
                       //                     tag: ['ubuntu-test'], 
                       //                     build_args: ["base=ubuntu",
                       //                                  "tag=bionic",
                       //                                  "branch=test"])
                    }
                 }
            }
        }

        stage('Docker Hub delivery') {
            when {
                anyOf {
                    branch 'master'
                    branch 'test'
                    buildingTag()
                }
            }
            steps{
                script {
                    DockerPush(id_deb)
                    //DockerPush(id_ubuntu)
                }
            }
            post {
                failure {
                    DockerClean()
                }
                always {
                    cleanWs()
                }
            }
        }

    }

    post {
        failure {
            script {
                currentBuild.result = 'FAILURE'
            }
        }

        always  {
            script { //stage("Email notification")
                def build_status =  currentBuild.result
                build_status =  build_status ?: 'SUCCESS'
                def subject = """
New ${app_name} build in Jenkins@EOSC-Synergy:\
${build_status}: Job '${env.JOB_NAME}\
[${env.BUILD_NUMBER}]'"""

                def body = """
Dear ${author_name},\n\n
A new build of '${app_name} (${env.BRANCH_NAME})' application is available in Jenkins at:\n\n
*  ${env.BUILD_URL}\n\n
terminated with '${build_status}' status.\n\n
Check console output at:\n\n
*  ${env.BUILD_URL}/console\n\n

Jenkins CI/CD service"""

                EmailSend(subject, body, "${author_email}")
            }
        }
    }
}
