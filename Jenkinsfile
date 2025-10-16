pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
            }
        }
        
        stage('Environment Setup') {
            steps {
                script {
                    // Create virtual environment
                    sh """
                        python${PYTHON_VERSION} -m venv venv
                        source venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest pytest-cov flake8 bandit safety
                    """
                }
            }
        }
        
        stage('Code Quality Checks') {
            parallel {
                stage('Linting') {
                    steps {
                        script {
                            sh """
                                source venv/bin/activate
                                flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                                flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
                            """
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        script {
                            sh """
                                source venv/bin/activate
                                bandit -r . -f json -o bandit-report.json || true
                                safety check --json --output safety-report.json || true
                            """
                        }
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: '.',
                                reportFiles: 'bandit-report.json',
                                reportName: 'Bandit Security Report'
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                script {
                    sh """
                        source venv/bin/activate
                        pytest tests/ -v --cov=. --cov-report=xml --cov-report=html --junitxml=test-results.xml
                    """
                }
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'test-results.xml'
                    publishCoverage adapters: [
                        coberturaAdapter('coverage.xml')
                    ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Build and Package') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                script {
                    // Create deployment package
                    sh """
                        # Create deployment directory
                        mkdir -p deploy
                        
                        # Copy application files
                        cp -r . deploy/
                        cd deploy
                        
                        # Remove unnecessary files
                        rm -rf .git .venv venv __pycache__ .pytest_cache
                        rm -rf tests/ .flake8 pytest.ini Jenkinsfile
                        rm -rf docker-compose.yml Dockerfile k8s/
                        
                        # Create deployment archive
                        tar -czf ../stock-market-app-${BUILD_NUMBER}.tar.gz .
                        cd ..
                    """
                }
            }
        }
        
        stage('Integration Tests') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                script {
                    // Run local integration tests
                    sh """
                        # Test Streamlit app locally
                        python -c "
                        import streamlit as st
                        import yfinance as yf
                        import pandas as pd
                        import plotly.graph_objs as go
                        from plotly.subplots import make_subplots
                        print('All imports successful')
                        "
                        
                        # Test basic functionality
                        python -c "
                        import yfinance as yf
                        ticker = yf.Ticker('AAPL')
                        info = ticker.info
                        print('Yahoo Finance API test successful')
                        "
                    """
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    sh """
                        # Trigger Render.com staging deployment
                        echo "Deploying to Render.com staging environment..."
                        echo "Note: Configure RENDER_DEPLOY_HOOK_STAGING credential to enable deployment"
                        
                        # Wait for deployment to complete
                        echo "Waiting for staging deployment to complete..."
                        sleep 5
                        
                        # Verify deployment
                        echo "Staging deployment would be triggered here"
                    """
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Manual approval for production deployment
                    input message: 'Deploy to production?', ok: 'Deploy'
                    
                    sh """
                        # Trigger Render.com production deployment
                        echo "Deploying to Render.com production environment..."
                        echo "Note: Configure RENDER_DEPLOY_HOOK_PRODUCTION credential to enable deployment"
                        
                        # Wait for deployment to complete
                        echo "Waiting for production deployment to complete..."
                        sleep 5
                        
                        # Verify deployment
                        echo "Production deployment would be triggered here"
                    """
                }
            }
        }
    }
    
    post {
        always {
            // Cleanup
            sh """
                rm -rf venv || true
                rm -rf deploy || true
                rm -f stock-market-app-*.tar.gz || true
            """
        }
        
        success {
            echo "✅ Build completed successfully!"
        }
        
        failure {
            echo "❌ Build failed!"
        }
        
        unstable {
            echo "⚠️ Build unstable!"
        }
    }
}
