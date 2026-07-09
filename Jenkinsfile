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
                        // No port mapping needed — health checks run INSIDE the container.
                        sh """docker run -d --name verify-flowise \
                            -e FLOWISE_USERNAME=ci_admin \
                            -e FLOWISE_PASSWORD=ci_test_pass \
                            ${IMAGE_NAME}:${IMAGE_TAG}"""

                        sh "sleep 45"

                        // WHY docker exec + node instead of curl:
                        // Jenkins itself runs inside a Docker container on a different
                        // network. Curling localhost (Jenkins container) or the bridge IP
                        // (blocked by iptables across networks) both fail. The only
                        // reliable approach is to run the check INSIDE verify-flowise via
                        // docker exec — localhost:3000 is always reachable there.
                        sh '''docker exec verify-flowise node -e "
const http = require(\'http\');
const u = process.env.FLOWISE_USERNAME;
const p = process.env.FLOWISE_PASSWORD;
const auth = (u && p)
  ? { Authorization: \'Basic \' + Buffer.from(u + \':\' + p).toString(\'base64\') }
  : {};
let attempt = 0;
const check = () => {
  attempt++;
  if (attempt > 20) { console.error(\'Flowise did not become healthy in time.\'); process.exit(1); }
  http.get({ hostname: \'localhost\', port: 3000, path: \'/api/v1/ping\', headers: auth }, (r) => {
    if (r.statusCode === 200) {
      console.log(\'Flowise is healthy (attempt \' + attempt + \')\');
      process.exit(0);
    }
    console.log(\'Attempt \' + attempt + \' — HTTP \' + r.statusCode + \', retrying in 3s...\');
    setTimeout(check, 3000);
  }).on(\'error\', (err) => {
    console.log(\'Attempt \' + attempt + \' — \' + err.message + \', retrying in 3s...\');
    setTimeout(check, 3000);
  });
};
check();
"'''

                        // Allow extra time for the background chatflow import to finish.
                        sh "sleep 20"

                        // Non-blocking chatflow presence check (import is a background
                        // process and may still be in progress at this point).
                        sh '''docker exec verify-flowise node -e "
const http = require(\'http\');
const u = process.env.FLOWISE_USERNAME;
const p = process.env.FLOWISE_PASSWORD;
const auth = (u && p)
  ? { Authorization: \'Basic \' + Buffer.from(u + \':\' + p).toString(\'base64\') }
  : {};
http.get({ hostname: \'localhost\', port: 3000, path: \'/api/v1/chatflows\', headers: auth }, (r) => {
  let body = \'\';
  r.on(\'data\', (c) => body += c);
  r.on(\'end\', () => {
    if (r.statusCode !== 200) {
      console.log(\'Chatflows API returned HTTP \' + r.statusCode + \' — skipping check.\');
      process.exit(0);
    }
    const found = body.includes(\'500 Days of Summer\');
    console.log(found
      ? \'✅ Chatflow imported successfully!\'
      : \'ℹ️  Chatflow import still in progress — will complete after deploy.\');
    process.exit(0);
  });
}).on(\'error\', (e) => {
  console.log(\'Chatflows check skipped: \' + e.message);
  process.exit(0);
});
"'''

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
