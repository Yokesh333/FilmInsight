pipeline {
    agent any

    environment {
        // Repository URL (properly quoted to avoid syntax errors)
        GITHUB_REPO = 'https://github.com/Yokesh333/FilmInsight-AI-Movie-Understanding-Assistant-using-LLMs.git'

        // Docker registry configurations (defaulting to Docker Hub)
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_NAME      = 'cinequery-ai-flowise'
        IMAGE_TAG       = "${BUILD_NUMBER}"
        REGISTRY_CREDENTIALS_ID = 'docker-hub-credentials'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint & Validate') {
            steps {
                echo 'Validating chatflow JSON configuration...'
                // Simple validation to ensure the JSON is not malformed
                sh 'node -e "JSON.parse(require(\'fs\').readFileSync(\'500DaysofSummer Chatflow.json\', \'utf8\'))"'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
                script {
                    // Standard Pipeline syntax (requires Docker Pipeline plugin):
                    app = docker.build("${IMAGE_NAME}:${IMAGE_TAG}", "-f Dockerfile .")
                    
                    // Backup shell command if the Docker Pipeline plugin is not installed:
                    // sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile ."
                }
            }
        }

        stage('Test & Verify') {
            steps {
                echo 'Verifying that Flowise starts up correctly and the import logic works...'
                script {
                    // Standard Pipeline syntax (requires Docker Pipeline plugin):
                    docker.image("${IMAGE_NAME}:${IMAGE_TAG}").withRun('-p 3000:3000') { c ->
                        // Wait for server initialization
                        sh 'sleep 15'
                        // Hit the ping endpoint to verify container health
                        sh 'curl --retry 5 --retry-delay 3 http://localhost:3000/api/v1/ping'
                        // Check if the chatflow was successfully imported
                        sh 'curl -s http://localhost:3000/api/v1/chatflows | grep "500 Days of Summer Chatflow"'
                    }

                    // Backup shell command alternative:
                    // sh "docker run -d --name verify-flowise -p 3000:3000 ${IMAGE_NAME}:${IMAGE_TAG}"
                    // sh "sleep 15"
                    // sh "curl --retry 5 --retry-delay 3 http://localhost:3000/api/v1/ping"
                    // sh "curl -s http://localhost:3000/api/v1/chatflows | grep '500 Days of Summer Chatflow'"
                    // sh "docker rm -f verify-flowise"
                }
            }
        }

        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                echo "Pushing image to registry ${DOCKER_REGISTRY}..."
                script {
                    // Standard Pipeline syntax:
                    docker.withRegistry("https://${DOCKER_REGISTRY}", REGISTRY_CREDENTIALS_ID) {
                        app.push("${IMAGE_TAG}")
                        app.push("latest")
                    }

                    // Backup shell command alternative:
                    // sh "docker login -u \$DOCKER_USER -p \$DOCKER_PASS ${DOCKER_REGISTRY}"
                    // sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                    // sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
                    // sh "docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                    // sh "docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying to staging/production environment...'
                // Customize this stage with your own deployment command.
                // Examples:
                // sh 'docker compose down && docker compose up -d'
                // sh 'kubectl rollout restart deployment/flowise-deployment'
            }
        }
    }

    post {
        always {
            echo 'Cleaning up built images locally to save disk space...'
            sh "docker rmi -f ${IMAGE_NAME}:${IMAGE_TAG} || true"
        }
        success {
            echo 'Jenkins Pipeline completed successfully! CineQuery AI deployed.'
        }
        failure {
            echo 'Pipeline failed. Please inspect build and container logs.'
        }
    }
}
