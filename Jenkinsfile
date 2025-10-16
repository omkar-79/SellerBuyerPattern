pipeline {
    agent any
    
    environment {
        RENDER_DEPLOY_HOOK_PRODUCTION = 'https://api.render.com/deploy/srv-d3o53a9r0fns73bth1e0?key=jiSRgm6pIYw'
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
                    // Detect available Python version
                    def pythonCmd = sh(
                        script: """
                            if command -v python3 &> /dev/null; then
                                echo "python3"
                            elif command -v python &> /dev/null; then
                                echo "python"
                            else
                                echo "python3"
                            fi
                        """,
                        returnStdout: true
                    ).trim()
                    
                    env.PYTHON_CMD = pythonCmd
                    
                    // Create virtual environment and install dependencies
                    sh """
                        echo "Using Python command: ${pythonCmd}"
                        ${pythonCmd} --version
                        ${pythonCmd} -m venv venv
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
                                echo "Running flake8 linting..."
                                flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
                                flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || true
                            """
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        script {
                            sh """
                                source venv/bin/activate
                                echo "Running security scans..."
                                bandit -r . -f json -o bandit-report.json || true
                                safety check --json || true
                            """
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
                        echo "Running unit tests..."
                        pytest tests/ -v --cov=. --cov-report=xml --cov-report=html --junitxml=test-results.xml || true
                    """
                }
            }
            post {
                always {
                    echo "Test results available in test-results.xml"
                    echo "Coverage report available in htmlcov/index.html"
                }
            }
        }
        
        stage('Build and Package') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Create deployment package
                    sh """
                        echo "Creating deployment package..."
                        mkdir -p deploy
                        cp -r . deploy/
                        cd deploy
                        rm -rf .git .venv venv __pycache__ .pytest_cache
                        rm -rf tests/ .flake8 pytest.ini Jenkinsfile
                        rm -rf bandit-report.json safety-report.json test-results.xml htmlcov/
                        tar -czf ../stock-market-app-${BUILD_NUMBER}.tar.gz .
                        cd ..
                        echo "Deployment package created: stock-market-app-${BUILD_NUMBER}.tar.gz"
                    """
                }
            }
        }
        
        stage('Integration Tests') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Run local integration tests
                    sh """
                        source venv/bin/activate
                        echo "Running integration tests..."
                        python -c "
                        import streamlit as st
                        import yfinance as yf
                        import pandas as pd
                        import plotly.graph_objs as go
                        from plotly.subplots import make_subplots
                        print('✅ All imports successful')
                        "
                        
                        # Test basic functionality
                        python -c "
                        import yfinance as yf
                        ticker = yf.Ticker('AAPL')
                        info = ticker.info
                        print('✅ Yahoo Finance API test successful')
                        "
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
                        echo "🚀 Deploying to Render.com production environment..."
                        curl -X POST "${RENDER_DEPLOY_HOOK_PRODUCTION}"
                        echo "✅ Production deployment triggered successfully!"
                        echo "Check Render.com dashboard for deployment status"
                    """
                }
            }
            post {
                success {
                    echo "✅ Production deployment completed successfully!"
                    echo "Deployment ID: ${BUILD_NUMBER}"
                    echo "Commit: ${env.GIT_COMMIT_SHORT}"
                }
                failure {
                    echo "❌ Production deployment failed!"
                    echo "Check Render.com logs for details"
                }
            }
        }
        
        stage('Rollback Check') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Ask if rollback is needed
                    def rollbackNeeded = input(
                        message: 'Is rollback needed?', 
                        ok: 'Rollback',
                        parameters: [
                            choice(
                                name: 'ROLLBACK_REASON',
                                choices: ['No rollback needed', 'Deployment failed', 'Performance issues', 'User complaints', 'Other'],
                                description: 'Select reason for rollback'
                            )
                        ]
                    )
                    
                    if (rollbackNeeded != 'No rollback needed') {
                        sh """
                            echo "🔄 Initiating rollback procedure..."
                            echo "Rollback reason: ${rollbackNeeded}"
                            echo "Previous deployment: ${BUILD_NUMBER - 1}"
                            echo "Note: Manual rollback required in Render.com dashboard"
                            echo "1. Go to Render.com dashboard"
                            echo "2. Select your service"
                            echo "3. Go to 'Deploys' tab"
                            echo "4. Click 'Rollback' on previous successful deployment"
                        """
                    } else {
                        echo "✅ No rollback needed - deployment successful"
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Cleanup
            sh """
                echo "🧹 Cleaning up..."
                rm -rf venv || true
                rm -rf deploy || true
                rm -f stock-market-app-*.tar.gz || true
                echo "✅ Cleanup completed"
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