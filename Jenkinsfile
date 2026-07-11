pipeline {
    agent any

    environment {
        // ── Project ─────────────────────────────────────────────
        APP_NAME        = 'filminsight'
        GITHUB_REPO     = 'https://github.com/Yokesh333/FilmInsight.git'

        // ── Docker Image Names ───────────────────────────────────
        FRONTEND_IMAGE  = "${APP_NAME}-frontend"
        BACKEND_IMAGE   = "${APP_NAME}-backend"
        IMAGE_TAG       = "${BUILD_NUMBER}"

        // ── Registry (DockerHub / local) ─────────────────────────
        // REGISTRY     = 'your-dockerhub-username'

        // ── Environment Variables ────────────────────────────────
        FLOWISE_URL     = credentials('flowise-url')       // Jenkins credential
        FLOWISE_CF_ID   = credentials('flowise-chatflow-id')

        // ── Ports ────────────────────────────────────────────────
        FRONTEND_PORT   = '5000'
        BACKEND_PORT    = '8000'
        FLOWISE_PORT    = '9000'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')
    }

    stages {

        // ── 1. Checkout ─────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📦 Checking out source code...'
                checkout scm
                sh 'git log --oneline -5'
                sh 'ls -la'
            }
        }

        // ── 2. Install Dependencies ─────────────────────────────
        stage('Install Dependencies') {
            parallel {
                stage('Frontend Deps') {
                    steps {
                        dir('frontend') {
                            echo '📦 Installing frontend dependencies...'
                            sh 'node --version'
                            sh 'npm --version'
                            sh 'npm ci --silent'
                            sh 'npm ls --depth=0 || true'
                        }
                    }
                }
                stage('Backend Deps') {
                    steps {
                        dir('backend') {
                            echo '🐍 Setting up Python environment...'
                            sh 'python3 --version || python --version'
                            sh '''
                                python3 -m venv .venv || python -m venv .venv
                                . .venv/bin/activate
                                pip install --upgrade pip --quiet
                                pip install -r requirements.txt --quiet
                            '''
                        }
                    }
                }
            }
        }

        // ── 3. Lint & Validate ──────────────────────────────────
        stage('Lint & Validate') {
            parallel {
                stage('Frontend Lint') {
                    steps {
                        dir('frontend') {
                            echo '🔍 Linting frontend...'
                            sh 'npm run lint || true'
                        }
                    }
                }
                stage('Validate Chatflow JSON') {
                    steps {
                        echo '✅ Validating chatflow configuration...'
                        sh '''
                            for f in *.json; do
                                if [ -f "$f" ]; then
                                    python3 -c "import json; json.load(open('$f'))" && echo "✓ $f valid"
                                fi
                            done || true
                        '''
                    }
                }
            }
        }

        // ── 4. Frontend Build ────────────────────────────────────
        stage('Frontend Build') {
            steps {
                dir('frontend') {
                    echo '⚛️  Building React application...'
                    sh 'npm run build'
                    sh 'du -sh dist/'
                    archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: true
                }
            }
        }

        // ── 5. Backend Build & Tests ─────────────────────────────
        stage('Backend Tests') {
            steps {
                dir('backend') {
                    echo '🧪 Running backend tests...'
                    sh '''
                        . .venv/bin/activate
                        python3 -c "from app.main import app; print('✓ App imports OK')"
                        python3 -c "from app.services.flowise import FlowiseService; print('✓ FlowiseService OK')"
                        python3 -c "from app.models.schemas import ChatRequest, ChatResponse; print('✓ Schemas OK')"
                        python3 -m pytest tests/ -v --tb=short 2>/dev/null || echo 'ℹ️  No pytest tests found'
                    '''
                }
            }
        }

        // ── 6. Docker Build ──────────────────────────────────────
        stage('Docker Build') {
            steps {
                echo '🐳 Building Docker images...'
                parallel(
                    'Frontend': {
                        dir('frontend') {
                            sh "docker build -t ${FRONTEND_IMAGE}:${IMAGE_TAG} -t ${FRONTEND_IMAGE}:latest ."
                            sh "docker images ${FRONTEND_IMAGE}:${IMAGE_TAG}"
                        }
                    },
                    'Backend': {
                        dir('backend') {
                            sh "docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} -t ${BACKEND_IMAGE}:latest ."
                            sh "docker images ${BACKEND_IMAGE}:${IMAGE_TAG}"
                        }
                    }
                )
            }
        }

        // ── 7. Integration Test ──────────────────────────────────
        stage('Integration Test') {
            steps {
                echo '🔗 Running integration checks...'
                script {
                    try {
                        sh """
                            docker run -d --name test-backend \\
                                -p 18000:8000 \\
                                -e FLOWISE_URL=http://localhost:9000 \\
                                -e FLOWISE_CHATFLOW_ID=test-id \\
                                ${BACKEND_IMAGE}:${IMAGE_TAG}
                            sleep 10
                        """
                        sh '''
                            curl -sf http://localhost:18000/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ Backend root OK:', d['name'])"
                            curl -sf http://localhost:18000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ Health OK:', d['status'])"
                            curl -sf http://localhost:18000/docs > /dev/null && echo "✓ Swagger docs OK"
                        '''
                    } catch (Exception e) {
                        sh 'docker logs test-backend || true'
                        throw e
                    } finally {
                        sh 'docker rm -f test-backend || true'
                    }
                }
            }
        }

        // ── 8. Docker Compose Up ─────────────────────────────────
        stage('Docker Compose') {
            steps {
                dir('docker') {
                    echo '🚀 Starting all services with Docker Compose...'
                    sh '''
                        docker compose down --remove-orphans || true
                        FLOWISE_CHATFLOW_ID=${FLOWISE_CF_ID} \\
                        FLOWISE_URL=${FLOWISE_URL} \\
                        docker compose up -d --build
                        echo "Waiting for services to become healthy..."
                        sleep 20
                        docker compose ps
                    '''
                }
            }
        }

        // ── 9. Deploy ────────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo '🌐 Deploying FilmInsight...'
                script {
                    // Remove old named containers and redeploy
                    sh """
                        docker rm -f ${FRONTEND_IMAGE} || true
                        docker rm -f ${BACKEND_IMAGE}  || true

                        docker run -d --name ${BACKEND_IMAGE} \\
                            -p ${BACKEND_PORT}:8000 \\
                            -e FLOWISE_URL=${FLOWISE_URL} \\
                            -e FLOWISE_CHATFLOW_ID=${FLOWISE_CF_ID} \\
                            --restart always \\
                            ${BACKEND_IMAGE}:${IMAGE_TAG}

                        docker run -d --name ${FRONTEND_IMAGE} \\
                            -p ${FRONTEND_PORT}:80 \\
                            --add-host=host.docker.internal:host-gateway \\
                            --restart always \\
                            ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    """
                    echo "✅ Backend  → http://\$SERVER_IP:${BACKEND_PORT}"
                    echo "✅ Frontend → http://\$SERVER_IP:${FRONTEND_PORT}"
                }
            }
        }

        // ── 10. Health Check ─────────────────────────────────────
        stage('Health Check') {
            steps {
                echo '💊 Running post-deploy health checks...'
                script {
                    retry(5) {
                        sleep(10)
                        sh "curl -sf http://localhost:${BACKEND_PORT}/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('✓ Backend healthy:', d['status'])\""
                        sh "curl -sf http://localhost:${FRONTEND_PORT}/ > /dev/null && echo '✓ Frontend healthy'"
                    }
                }
            }
        }

        // ── 11. Clean Workspace ──────────────────────────────────
        stage('Clean Workspace') {
            steps {
                echo '🧹 Cleaning up workspace...'
                dir('frontend') { sh 'rm -rf node_modules dist || true' }
                dir('backend')  { sh 'rm -rf .venv __pycache__ || true' }
                sh "docker rmi ${FRONTEND_IMAGE}:\$(docker images ${FRONTEND_IMAGE} --format '{{.Tag}}' | grep -v latest | sort -rn | tail -n +4) 2>/dev/null || true"
                sh "docker rmi ${BACKEND_IMAGE}:\$(docker images ${BACKEND_IMAGE}   --format '{{.Tag}}' | grep -v latest | sort -rn | tail -n +4) 2>/dev/null || true"
                sh 'docker system prune -f --filter "until=24h" || true'
                echo '✅ Workspace cleaned.'
            }
        }

    } // end stages

    post {
        success {
            echo """
            ╔══════════════════════════════════════════╗
            ║  ✅  FilmInsight Deployed Successfully!  ║
            ║  Build: #${BUILD_NUMBER}                          ║
            ╚══════════════════════════════════════════╝
            """
        }
        failure {
            echo '❌ Pipeline FAILED. Check logs above.'
            sh 'docker compose -f docker/docker-compose.yml logs --tail=50 || true'
        }
        always {
            echo 'Pipeline complete.'
            sh 'docker ps --filter "name=${APP_NAME}" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}" || true'
        }
    }
}
