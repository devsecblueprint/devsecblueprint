// For Damien's Personal Homelab
pipeline {
    agent any

    environment {
       KUBECONFIG = '/home/jenkins/.kubeconfig'
       GIT_SSL_NO_VERIFY = 'true'
       SONAR_TOKEN = credentials('sonar-analysis')
       SONAR_PROJECT_KEY = 'devsecblueprint.github.io'
       DOCKER_IMAGE_NAME = 'devsecblueprint'
       NEXUS_DOCKER_PUSH_INDEX = 'nexus-dockerhost.dsb-hub.local'
       NEXUS_DOCKER_PUSH_PATH = 'repository/docker-host'
       GOOGLE_ANALYTICS_ID = "test"
       GOOGLE_TAG_MANAGER_ID = "test"
    }

    options {
        disableConcurrentBuilds()
    }

    stages {
        stage('Clone') {
            steps {
                checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'Gitea PAT', url: 'https://dsb-hub.local/damien/devsecblueprint.github.io.git']])
            }
        }
        stage('Build') {
            steps {
                sh """
                echo "GOOGLE_ANALYTICS_ID=${GOOGLE_ANALYTICS_ID}" > .env
                echo "GOOGLE_TAG_MANAGER_ID=${GOOGLE_TAG_MANAGER_ID}" >> .env
                cat .env
                """
                sh 'docker build -t ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }
        stage('Security Scan'){
            parallel {
                stage('Sonar Scan') {
                    steps {
                        script {
                            try{
                                withSonarQubeEnv(installationName: 'Sonar Server', credentialsId: 'sonar-analysis') {
                                    sh '''
                                    docker run --rm \
                                    -e SONAR_HOST_URL="${SONAR_HOST_URL}" \
                                    -e SONAR_TOKEN="${SONAR_TOKEN}" \
                                    -v "$(pwd):/usr/src" \
                                    ${NEXUS_DOCKER_PUSH_INDEX}/repository/docker-host/sonar-scanner-cli \
                                    -Dsonar.projectKey="${SONAR_PROJECT_KEY}" \
                                    -Dsonar.qualitygate.wait=true \
                                    -Dsonar.sources=.
                                    '''
                                }
                            } catch (Exception e) {
                                // Handle the error
                                echo "Quality Qate check has failed: ${e}"
                                currentBuild.result = 'UNSTABLE' // Mark the build as unstable instead of failing
                            }
                        }
                    }
                }
                stage('Security Scan') {
                    steps {
                        sh '''
                            trivy image --severity HIGH,CRITICAL ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}
                        '''
                    }
                }
            }
        }
        stage('Publish') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'nexus', passwordVariable: 'NEXUS_PASSWORD', usernameVariable: 'NEXUS_USERNAME')]) {
                        sh """
                        docker login ${NEXUS_DOCKER_PUSH_INDEX} -u $NEXUS_USERNAME -p $NEXUS_PASSWORD
                        docker tag ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} ${NEXUS_DOCKER_PUSH_INDEX}/${NEXUS_DOCKER_PUSH_PATH}/${DOCKER_IMAGE_NAME}:latest
                        docker push ${NEXUS_DOCKER_PUSH_INDEX}/${NEXUS_DOCKER_PUSH_PATH}/${DOCKER_IMAGE_NAME}:latest
                        """
                    }
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    echo 'Deploying to DSB Node 01'
                    sh '''
                    helm upgrade --install ${DOCKER_IMAGE_NAME} ./helm/
                    '''
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}