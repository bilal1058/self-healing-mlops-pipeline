pipeline {
    agent any

    environment {
        DOCKER_IMAGE_UNSTABLE = "bilal888/sentiment-api:unstable"
        DOCKER_IMAGE_STABLE = "bilal888/sentiment-api:stable"
    }

    stages {
        stage('Fetch') {
            steps {
                checkout scm
            }
        }

        stage('Build and Run') {
            steps {
                sh '''
                docker rm -f sentiment-test || true
                docker build -t sentiment-api:test .
                docker run -d --name sentiment-test -p 5000:5000 sentiment-api:test
                sleep 30
                curl -f http://localhost:5000/health
                '''
            }
        }

        stage('Unit Test') {
            steps {
              sh '''
		docker exec sentiment-test pytest tests/test_api.py'''
            }
        }

        stage('UI Test') {
            steps {
                sh '''
		        docker exec sentiment-test python -m pytest tests/test_ui.py || true
                  '''
            }
        }

        stage('Build and Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                    docker build -t $DOCKER_IMAGE_UNSTABLE .
                    docker push $DOCKER_IMAGE_UNSTABLE

                    git fetch origin stable-fallback
                    git checkout stable-fallback
                    docker build -t $DOCKER_IMAGE_STABLE .
                    docker push $DOCKER_IMAGE_STABLE

                    git checkout main
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                kubectl apply -f k8s/pvc.yaml
                kubectl apply -f k8s/blue-deployment.yaml
                kubectl apply -f k8s/green-deployment.yaml
                kubectl apply -f k8s/service.yaml
                kubectl get pods
                kubectl get svc sentiment-api-service
                '''
            }
        }
    }

    post {
        always {
            sh 'docker rm -f sentiment-test || true'
        }
    }
}
