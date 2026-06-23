pipeline {
    agent any

    environment {
        DOCKER_IMAGE_UNSTABLE = "bilal888/sentiment-api:unstable"
        DOCKER_IMAGE_STABLE = "bilal888/sentiment-api:stable"
        BASE_URL = "http://localhost:5000"
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
                echo "Waiting for application..."
				for i in $(seq 1 60); do
				    if curl -fs http://localhost:5000/health > /dev/null; then
				        echo "Application is ready."
				        break
				    fi
				    echo "Attempt $i: service not ready yet..."
				    sleep 2
				done
                curl -f http://localhost:5000/health
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                rm -rf venv
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install pytest requests
                BASE_URL=http://localhost:5000 pytest tests/test_api.py
                '''
            }
        }

        stage('UI Test') {
            steps {
                sh '''
                . venv/bin/activate
                pip install selenium
                BASE_URL=http://localhost:5000 pytest tests/test_ui.py
                '''
            }
        }

        stage('Build and Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                    docker tag sentiment-api:test $DOCKER_IMAGE_UNSTABLE
                    docker push $DOCKER_IMAGE_UNSTABLE

                    git fetch origin stable-fallback
	            	git checkout -B stable-fallback origin/stable-fallback
                    docker build -t $DOCKER_IMAGE_STABLE .
                    docker push $DOCKER_IMAGE_STABLE

                    git checkout -B main origin/main
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
                kubectl rollout status deployment/sentiment-blue-deployment --timeout=300s
                kubectl rollout status deployment/sentiment-green-deployment --timeout=300s
                kubectl get pods
                kubectl get svc sentiment-api-service
                echo "Waiting for service..."
				for i in $(seq 1 60); do
				    if curl -fs http://35.154.1.53:32500/health > /dev/null; then
				        echo "Service is healthy."
				        break
				    fi
				    echo "Attempt $i: service not ready..."
				    sleep 5
				done
                curl -f http://35.154.1.53:32500/health
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
