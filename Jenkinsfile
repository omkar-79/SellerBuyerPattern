pipeline {
    agent any
    
    environment {
        RENDER_DEPLOY_HOOK_PRODUCTION = credentials('RENDER_DEPLOY_HOOK_PRODUCTION')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Environment Setup') {
            steps {
                sh """
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov flake8 bandit safety
                """
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Linting') {
                    steps {
                        sh """
                            source venv/bin/activate
                            flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
                        """
                    }
                }
                
                stage('Security') {
                    steps {
                        sh """
                            source venv/bin/activate
                            bandit -r . -f json -o bandit-report.json || true
                            safety check --json || true
                        """
                    }
                }
            }
        }
        
        stage('Tests') {
            steps {
                sh """
                    source venv/bin/activate
                    pytest tests/ -v --cov=. --cov-report=xml --cov-report=html --junitxml=test-results.xml || true
                """
            }
        }
        
        stage('Build') {
            steps {
                sh """
                    rm -rf deploy
                    mkdir -p deploy
                    rsync -av --exclude=deploy --exclude=.git --exclude=.venv --exclude=venv --exclude=__pycache__ --exclude=.pytest_cache --exclude=tests --exclude=.flake8 --exclude=pytest.ini --exclude=Jenkinsfile --exclude=bandit-report.json --exclude=safety-report.json --exclude=test-results.xml --exclude=htmlcov --exclude='*.tar.gz' . deploy/
                    cd deploy
                    tar -czf ../stock-market-app-${BUILD_NUMBER}.tar.gz .
                    cd ..
                    echo "Deployment package created: stock-market-app-${BUILD_NUMBER}.tar.gz"
                """
            }
        }
        
        stage('Integration Test') {
            steps {
                sh """
                    source venv/bin/activate
                    python -c "import streamlit as st; import yfinance as yf; import pandas as pd; import plotly.graph_objs as go; from plotly.subplots import make_subplots; print('All imports successful')"
                    python -c "import yfinance as yf; ticker = yf.Ticker('AAPL'); info = ticker.info; print('Yahoo Finance API test successful')"
                """
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    input message: 'Deploy to production?', ok: 'Deploy'
                    sh """
                        curl -X POST "${RENDER_DEPLOY_HOOK_PRODUCTION}"
                        echo "Production deployment triggered successfully!"
                    """
                }
            }
        }
    }
    
    post {
        always {
            sh """
                rm -rf venv || true
                rm -rf deploy || true
                rm -f stock-market-app-*.tar.gz || true
            """
        }
        
        success {
            echo "Build completed successfully!"
        }
        
        failure {
            echo "Build failed!"
        }
    }
}
