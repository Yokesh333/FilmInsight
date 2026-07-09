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
                // --pull=missing: only pull the base image if it isn't cached locally.
                // This avoids the 36-minute re-download on every build.
                sh "docker build --pull=missing -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile ."
            }
        }

        stage('Test & Verify') {
            steps {
                echo 'Verifying that Flowise starts up correctly and the import logic works...'
                script {
                    try {
                        sh "docker run -d --name verify-flowise -p 9000:3000 ${IMAGE_NAME}:${IMAGE_TAG}"
                        // Flowise initialises the DB, runs migrations, and loads all
                        // nodes before it binds to the port — 45s is a safe minimum.
                        sh "sleep 45"
                        // --retry-connrefused: keep retrying even on 'Connection refused',
                        // not just on transient HTTP errors.
                        sh "curl --retry 10 --retry-delay 5 --retry-connrefused http://localhost:9000/api/v1/ping"
                        sh "curl -sf http://localhost:9000/api/v1/chatflows | grep '500 Days of Summer Chatflow'"
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
            echo 'Removing the built app image tag to free disk space...'
            // Only untag the app image — do NOT delete the base flowise image layers.
            // Keeping the base layers means the next build skips the 36-min download.
            sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
        }
        success {
            echo 'Jenkins Pipeline completed successfully! CineQuery AI deployed.'
        }
        failure {
            echo 'Pipeline failed. Please inspect build and container logs.'
        }
    }
}
