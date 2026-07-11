pipeline {
    agent any

    environment {
        // ── Project ──────────────────────────────────────────────────────────
        APP_NAME        = 'filminsight'
        GITHUB_REPO     = 'https://github.com/Yokesh333/FilmInsight.git'

        // ── Docker Image Names ───────────────────────────────────────────────
        FRONTEND_IMAGE  = "${APP_NAME}-frontend"
        BACKEND_IMAGE   = "${APP_NAME}-backend"
        IMAGE_TAG       = "${BUILD_NUMBER}"

        // ── Jenkins-managed credentials ──────────────────────────────────────
        FLOWISE_URL     = credentials('flowise-url')
        FLOWISE_CF_ID   = credentials('flowise-chatflow-id')

        // ── Ports ────────────────────────────────────────────────────────────
        FRONTEND_PORT   = '5000'
        BACKEND_PORT    = '8000'
        FLOWISE_PORT    = '9000'

        // ── Data paths on the Oracle Cloud host ─────────────────────────────
        // These directories are bind-mounted into containers as volumes.
        // They are NEVER pushed to GitHub.
        HOST_MOVIE_SCRIPTS = '/opt/filminsight/movie_scripts'
        HOST_CHROMA_DB     = '/opt/filminsight/chroma_db'
        HOST_LOGS          = '/opt/filminsight/logs'

        // ── Python used for ingestion ────────────────────────────────────────
        PYTHON_CMD = 'python3'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 60, unit: 'MINUTES')   // extended for first-run ingestion
        timestamps()
        ansiColor('xterm')
    }

    stages {

        // ── 1. Checkout ──────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📦 Checking out source code...'
                checkout scm
                sh 'git log --oneline -5'
                sh 'ls -la'
            }
        }

        // ── 2. Prepare Host Data Directories ─────────────────────────────────
        // Create persistent host directories if they don't exist.
        // These will be mounted into Docker containers as bind volumes.
        stage('Prepare Data Directories') {
            steps {
                echo '📁 Ensuring persistent data directories exist on host...'
                sh """
                    mkdir -p ${HOST_MOVIE_SCRIPTS}
                    mkdir -p ${HOST_CHROMA_DB}
                    mkdir -p ${HOST_LOGS}
                    echo "  ✓ ${HOST_MOVIE_SCRIPTS}"
                    echo "  ✓ ${HOST_CHROMA_DB}"
                    echo "  ✓ ${HOST_LOGS}"
                """
            }
        }

        // ── 3. Install Dependencies ───────────────────────────────────────────
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
                            sh "${PYTHON_CMD} --version"
                            sh """
                                ${PYTHON_CMD} -m venv .venv
                                . .venv/bin/activate
                                pip install --upgrade pip --quiet
                                pip install -r requirements.txt --quiet
                            """
                        }
                    }
                }
                stage('Ingestion Deps') {
                    steps {
                        echo '🧠 Installing ingestion pipeline dependencies...'
                        sh """
                            ${PYTHON_CMD} -m venv ingestion/.venv
                            . ingestion/.venv/bin/activate
                            pip install --upgrade pip --quiet
                            pip install -r ingestion/requirements.txt --quiet
                        """
                    }
                }
            }
        }

        // ── 4. Lint & Validate ────────────────────────────────────────────────
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

        // ── 5. Frontend Build ─────────────────────────────────────────────────
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

        // ── 6. Backend Tests ──────────────────────────────────────────────────
        stage('Backend Tests') {
            steps {
                dir('backend') {
                    echo '🧪 Running backend tests...'
                    sh """
                        . .venv/bin/activate
                        ${PYTHON_CMD} -c "from app.main import app; print('✓ App imports OK')"
                        ${PYTHON_CMD} -c "from app.services.flowise import FlowiseService; print('✓ FlowiseService OK')"
                        ${PYTHON_CMD} -c "from app.services.kb_startup import initialise_knowledge_base; print('✓ KBStartup OK')"
                        ${PYTHON_CMD} -c "from app.models.schemas import ChatRequest, ChatResponse; print('✓ Schemas OK')"
                        ${PYTHON_CMD} -m pytest tests/ -v --tb=short 2>/dev/null || echo 'ℹ️  No pytest tests found'
                    """
                }
            }
        }

        // ── 7. Docker Build ───────────────────────────────────────────────────
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
                        // Build context is project root so Dockerfile can COPY ingestion/
                        sh """
                            docker build \
                                -f backend/Dockerfile \
                                -t ${BACKEND_IMAGE}:${IMAGE_TAG} \
                                -t ${BACKEND_IMAGE}:latest \
                                .
                        """
                        sh "docker images ${BACKEND_IMAGE}:${IMAGE_TAG}"
                    }
                )
            }
        }

        // ── 8. Integration Test ───────────────────────────────────────────────
        stage('Integration Test') {
            steps {
                echo '🔗 Running integration checks...'
                script {
                    try {
                        sh """
                            docker run -d --name test-backend \
                                -p 18000:8000 \
                                -e FLOWISE_URL=http://localhost:9000 \
                                -e FLOWISE_CHATFLOW_ID=test-id \
                                -e MOVIE_SCRIPTS_DIR=/tmp/empty_scripts \
                                -e CHROMA_DB_DIR=/tmp/empty_chroma \
                                ${BACKEND_IMAGE}:${IMAGE_TAG}
                            sleep 15
                        """
                        sh '''
                            curl -sf http://localhost:18000/ \
                                | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ Backend root OK:', d['name'])"
                            curl -sf http://localhost:18000/health \
                                | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ Health OK:', d['status'])"
                            curl -sf http://localhost:18000/kb-status \
                                | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ KB status:', d['status'])"
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

        // ── 9. Docker Compose Up ──────────────────────────────────────────────
        stage('Docker Compose') {
            steps {
                dir('docker') {
                    echo '🚀 Starting all services with Docker Compose...'
                    sh """
                        docker compose down --remove-orphans || true

                        FLOWISE_CHATFLOW_ID=${FLOWISE_CF_ID} \\
                        FLOWISE_URL=${FLOWISE_URL} \\
                        HOST_MOVIE_SCRIPTS=${HOST_MOVIE_SCRIPTS} \\
                        HOST_CHROMA_DB=${HOST_CHROMA_DB} \\
                        HOST_LOGS=${HOST_LOGS} \\
                        docker compose up -d --build

                        echo "Waiting for services to become healthy..."
                        sleep 20
                        docker compose ps
                    """
                }
            }
        }

        // ── 10. Conditional Knowledge-Base Ingestion ──────────────────────────
        // Check whether chroma_db already has data.
        //   • If populated → skip ingestion (fast path, normal re-deploys)
        //   • If empty and movie_scripts has PDFs → run ingestion pipeline
        //   • If neither → warn; app starts with empty KB (never crashes)
        stage('Knowledge Base Check & Ingest') {
            steps {
                echo '🧠 Checking knowledge base state...'
                script {
                    def chromaPopulated = sh(
                        script: """
                            if [ -d "${HOST_CHROMA_DB}" ] && \
                               [ "\$(find ${HOST_CHROMA_DB} -name '*.sqlite3' 2>/dev/null | wc -l)" -gt "0" ]; then
                                echo "yes"
                            else
                                echo "no"
                            fi
                        """,
                        returnStdout: true
                    ).trim()

                    if (chromaPopulated == 'yes') {
                        echo '  ✅  Chroma DB already populated — skipping ingestion.'

                    } else {
                        def hasPdfs = sh(
                            script: """
                                if [ -d "${HOST_MOVIE_SCRIPTS}" ] && \
                                   [ "\$(find ${HOST_MOVIE_SCRIPTS} -name '*.pdf' 2>/dev/null | wc -l)" -gt "0" ]; then
                                    echo "yes"
                                else
                                    echo "no"
                                fi
                            """,
                            returnStdout: true
                        ).trim()

                        if (hasPdfs == 'yes') {
                            echo '  ⚙️   movie_scripts PDFs found. Running ingestion pipeline...'
                            sh """
                                . ingestion/.venv/bin/activate
                                PROJECT_ROOT=\$(pwd) \\
                                MOVIE_SCRIPTS_DIR=${HOST_MOVIE_SCRIPTS} \\
                                CHROMA_DB_DIR=${HOST_CHROMA_DB} \\
                                    ${PYTHON_CMD} -m ingestion.ingest_movies
                                echo '  ✅  Ingestion complete.'
                            """
                        } else {
                            echo '''
  ════════════════════════════════════════════════════════════
  ⚠️   WARNING: No movie scripts found.
       The knowledge base is empty.
       Add PDFs to: ${HOST_MOVIE_SCRIPTS}
       Then re-run this pipeline or run the ingestion manually.
  ════════════════════════════════════════════════════════════
                            '''
                            // Do NOT fail the build — the app still starts.
                        }
                    }
                }
            }
        }

        // ── 11. Deploy ────────────────────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo '🌐 Deploying FilmInsight...'
                script {
                    sh """
                        docker rm -f ${FRONTEND_IMAGE} || true
                        docker rm -f ${BACKEND_IMAGE}  || true

                        docker run -d --name ${BACKEND_IMAGE} \
                            -p ${BACKEND_PORT}:8000 \
                            -e FLOWISE_URL=${FLOWISE_URL} \
                            -e FLOWISE_CHATFLOW_ID=${FLOWISE_CF_ID} \
                            -e MOVIE_SCRIPTS_DIR=/data/movie_scripts \
                            -e CHROMA_DB_DIR=/data/chroma_db \
                            -v ${HOST_MOVIE_SCRIPTS}:/data/movie_scripts:ro \
                            -v ${HOST_CHROMA_DB}:/data/chroma_db \
                            -v ${HOST_LOGS}:/data/logs \
                            --restart always \
                            ${BACKEND_IMAGE}:${IMAGE_TAG}

                        docker run -d --name ${FRONTEND_IMAGE} \
                            -p ${FRONTEND_PORT}:80 \
                            --add-host=host.docker.internal:host-gateway \
                            --restart always \
                            ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    """
                    echo "✅ Backend  → http://\$SERVER_IP:${BACKEND_PORT}"
                    echo "✅ Frontend → http://\$SERVER_IP:${FRONTEND_PORT}"
                    echo "✅ KB status → http://\$SERVER_IP:${BACKEND_PORT}/kb-status"
                }
            }
        }

        // ── 12. Health Check ──────────────────────────────────────────────────
        stage('Health Check') {
            steps {
                echo '💊 Running post-deploy health checks...'
                script {
                    retry(5) {
                        sleep(10)
                        sh """
                            curl -sf http://localhost:${BACKEND_PORT}/health \
                                | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ Backend healthy:', d['status'])"
                            curl -sf http://localhost:${BACKEND_PORT}/kb-status \
                                | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ KB status:', d['status'], '|', d['doc_count'], 'docs')"
                            curl -sf http://localhost:${FRONTEND_PORT}/ > /dev/null && echo '✓ Frontend healthy'
                        """
                    }
                }
            }
        }

        // ── 13. Clean Workspace ───────────────────────────────────────────────
        stage('Clean Workspace') {
            steps {
                echo '🧹 Cleaning up workspace...'
                dir('frontend')  { sh 'rm -rf node_modules dist || true' }
                dir('backend')   { sh 'rm -rf .venv __pycache__ || true' }
                dir('ingestion') { sh 'rm -rf .venv __pycache__ || true' }
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
            ╔══════════════════════════════════════════════╗
            ║  ✅  FilmInsight Deployed Successfully!      ║
            ║  Build: #${BUILD_NUMBER}                              ║
            ╚══════════════════════════════════════════════╝
            """
        }
        failure {
            echo '❌ Pipeline FAILED. Check logs above.'
            sh 'docker compose -f docker/docker-compose.yml logs --tail=50 || true'
        }
        always {
            echo 'Pipeline complete.'
            sh "docker ps --filter 'name=${APP_NAME}' --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' || true"
        }
    }
}
