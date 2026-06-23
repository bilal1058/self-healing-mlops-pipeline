pipeline {
    agent any
    environment {
        DOCKER_IMAGE_UNSTABLE = "bilal888/sentiment-api:unstable"
        DOCKER_IMAGE_STABLE   = "bilal888/sentiment-api:stable"
        EC2_IP                = "35.154.1.53"
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
                    # Tool check
                    echo "=== Tool Check ==="
                    docker --version
                    kubectl version --client
                    python3 --version
                    echo "=== Tools OK ==="

                    docker rm -f sentiment-test || true

                    docker pull ${DOCKER_IMAGE_UNSTABLE} || true
                    docker build --cache-from ${DOCKER_IMAGE_UNSTABLE} -t sentiment-api:test .

                    docker run -d --name sentiment-test \
                        -p 5000:5000 \
                        -v sentiment-logs:/app/logs \
                        sentiment-api:test

                    echo "Waiting for application..."
                    for i in $(seq 1 40); do
                        if curl -sf http://localhost:5000/health > /dev/null; then
                            echo "App ready after $((i*3))s"
                            break
                        fi
                        echo "Attempt $i/40..."
                        sleep 3
                    done
                    curl -f http://localhost:5000/health
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    echo "=== Running unit tests inside container ==="
                    # Install pytest+requests inside the already-running container
                    docker exec sentiment-test pip install pytest requests --quiet

                    # Run tests inside the container (BASE_URL is localhost inside container)
                    docker exec \
                        -e BASE_URL=http://localhost:5000 \
                        sentiment-test \
                        python -m pytest tests/test_api.py -v
                '''
            }
        }

        stage('UI Test') {
            steps {
                sh '''
                    echo "=== Running UI tests via Selenium Docker image ==="
                    docker rm -f selenium-chrome || true

                    # Start Chrome in standalone mode (network=host so it reaches port 5000)
                    docker run -d --name selenium-chrome \
                        --network host \
                        -e SE_NODE_MAX_SESSIONS=1 \
                        selenium/standalone-chrome:latest

                    # Wait for Selenium to be ready
                    for i in $(seq 1 20); do
                        if curl -sf http://localhost:4444/wd/hub/status > /dev/null; then
                            echo "Selenium ready"
                            break
                        fi
                        echo "Waiting for Selenium... $i/20"
                        sleep 3
                    done

                    # Install selenium + pytest in a temp container that runs the test
                    docker run --rm \
                        --network host \
                        -v $(pwd)/tests:/tests \
                        -e BASE_URL=http://localhost:5000 \
                        -e SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub \
                        python:3.11-slim \
                        sh -c "pip install selenium pytest --quiet && python -m pytest /tests/test_ui.py -v"

                    docker rm -f selenium-chrome || true
                '''
            }
        }

        stage('Build and Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                        # Tag and push unstable (already built)
                        docker tag sentiment-api:test ${DOCKER_IMAGE_UNSTABLE}
                        docker push ${DOCKER_IMAGE_UNSTABLE} &
                        PUSH_UNSTABLE_PID=$!

                        # Build stable from a clean temp directory
                        rm -rf /tmp/stable-build
                        git clone --branch stable-fallback --depth 1 \
                            https://github.com/bilal1058/selfhealing-mlops-FA23-BAI-029.git \
                            /tmp/stable-build

                        docker pull ${DOCKER_IMAGE_STABLE} || true
                        docker build --cache-from ${DOCKER_IMAGE_STABLE} \
                            -t ${DOCKER_IMAGE_STABLE} /tmp/stable-build

                        wait $PUSH_UNSTABLE_PID
                        docker push ${DOCKER_IMAGE_STABLE}

                        rm -rf /tmp/stable-build
                        echo "Both images pushed successfully"
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    export KUBECONFIG=/var/lib/jenkins/.kube/config

                    kubectl apply -f k8s/pvc.yaml
                    kubectl apply -f k8s/blue-deployment.yaml
                    kubectl apply -f k8s/green-deployment.yaml
                    kubectl apply -f k8s/service.yaml

                    # Wait for both in parallel
                    kubectl rollout status deployment/sentiment-blue-deployment --timeout=300s &
                    kubectl rollout status deployment/sentiment-green-deployment --timeout=300s &
                    wait

                    kubectl get pods
                    kubectl get svc sentiment-api-service

                    echo "Waiting for NodePort 32500..."
                    for i in $(seq 1 40); do
                        if curl -sf http://${EC2_IP}:32500/health > /dev/null; then
                            echo "NodePort healthy at attempt $i"
                            break
                        fi
                        echo "Attempt $i/40..."
                        sleep 5
                    done
                    curl -f http://${EC2_IP}:32500/health
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f sentiment-test || true
                docker rm -f selenium-chrome || true
            '''
        }
    }
}
