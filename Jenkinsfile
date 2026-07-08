pipeline {
    agent any

    environment {
        // Repository URL
        GITHUB_REPO = 'https://github.com/Yokesh333/FilmInsight-AI-Movie-Understanding-Assistant-using-LLMs.git'

        IMAGE_NAME      = 'cinequery-ai-flowise'
        IMAGE_TAG       = "${BUILD_NUMBER}"
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
                sh '''
                    if command -v python3 >/dev/null 2>&1; then
                        python3 -c "import json; json.load(open('500DaysofSummer Chatflow.json'))"
                    elif command -v python >/dev/null 2>&1; then
                        python -c "import json; json.load(open('500DaysofSummer Chatflow.json'))"
                    elif command -v jq >/dev/null 2>&1; then
                        jq . "500DaysofSummer Chatflow.json" >/dev/null
                    elif command -v node >/dev/null 2>&1; then
                        node -e "JSON.parse(require('fs').readFileSync('500DaysofSummer Chatflow.json', 'utf8'))"
                    else
                        echo "Warning: No JSON validator (python3, python, jq, node) found. Skipping validation."
                    fi
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile ."
            }
        }

        stage('Test & Verify') {
            steps {
                echo 'Verifying that Flowise starts up correctly and the import logic works...'
                script {
                    try {
                        sh "docker run -d --name verify-flowise -p 9000:3000 ${IMAGE_NAME}:${IMAGE_TAG}"
                        sh "sleep 15"
                        sh "curl --retry 5 --retry-delay 3 http://localhost:9000/api/v1/ping"
                        sh "curl -s http://localhost:9000/api/v1/chatflows | grep '500 Days of Summer Chatflow'"
                    } catch (Exception e) {
                        echo "=== Container logs on failure ==="
                        sh "docker logs verify-flowise || true"
                        throw e
                    } finally {
                        sh "docker rm -f verify-flowise || true"
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying Flowise container locally...'
                sh "docker rm -f cinequery-ai-flowise || true"
                sh "docker run -d --name cinequery-ai-flowise -p 9000:3000 --restart always ${IMAGE_NAME}:${IMAGE_TAG}"
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
