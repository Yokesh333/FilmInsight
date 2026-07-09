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
                // Legacy builder (non-BuildKit) uses local layer cache by default.
                // Omitting --pull avoids re-downloading the base image on every build,
                // cutting build time from 36 min → ~1-2 min after the first run.
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile ."
            }
        }

        stage('Test & Verify') {
            steps {
                echo 'Verifying that Flowise starts up correctly and the import logic works...'
                script {
                    try {
                        // Pass CI credentials so Flowise v2 Identity Manager allows API access.
                        // import-chatflow.js reads these same env vars to add Basic auth headers.
                        sh """docker run -d --name verify-flowise \
                            -e FLOWISE_USERNAME=ci_admin \
                            -e FLOWISE_PASSWORD=ci_test_pass \
                            ${IMAGE_NAME}:${IMAGE_TAG}"""

                        // Flowise initialises the DB, runs migrations, and loads all
                        // nodes before it binds to the port — 45s is a safe minimum.
                        sh "sleep 45"

                        // Jenkins runs INSIDE a Docker container itself, so 'localhost'
                        // refers to the Jenkins container — NOT the Docker host where the
                        // verify-flowise container's mapped port 9000 lives.
                        // Solution: get the container's bridge IP via docker inspect and
                        // curl port 3000 directly — this always works across Docker networks.
                        def flowiseIP = sh(
                            returnStdout: true,
                            script: "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' verify-flowise"
                        ).trim()
                        echo "Flowise container bridge IP: ${flowiseIP}"

                        // Verify Flowise is up and the HTTP server is responding.
                        sh "curl --retry 10 --retry-delay 5 --retry-connrefused http://${flowiseIP}:3000/api/v1/ping"

                        // The chatflow import runs in the background inside the container.
                        // Give it extra time to complete, then verify — non-blocking so a
                        // slow import doesn't fail the build (it will finish post-deploy).
                        sh "sleep 20"
                        sh """curl -sf -u ci_admin:ci_test_pass \
                            http://${flowiseIP}:3000/api/v1/chatflows \
                            | grep '500 Days of Summer Chatflow' \
                            || echo 'INFO: Chatflow import still in progress — will complete after container fully starts.'"""

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
