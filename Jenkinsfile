pipeline {
    agent any
    
    environment {
        RENDER_DEPLOY_HOOK_PRODUCTION = credentials('RENDER_DEPLOY_HOOK_PRODUCTION')
        RENDER_API_KEY = credentials('RENDER_API_KEY')
        RENDER_SERVICE_ID = credentials('RENDER_SERVICE_ID')
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
                            echo "Running linting checks..."
                            flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
                            flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || true
                        """
                    }
                }
                
                stage('Security') {
                    steps {
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
        
        stage('Tests') {
            steps {
                sh """
                    source venv/bin/activate
                    pytest tests/ -v --cov=. --cov-report=xml --cov-report=html --junitxml=test-results.xml || true
                """
            }
        }
        
        stage('Code Review') {
            steps {
                script {
                    if (env.BRANCH_NAME == 'main') {
                        // Automatic code review for main branch
                        echo "Running automatic code review for main branch..."
                        
                        // Check if quality gates passed
                        sh """
                            source venv/bin/activate
                            
                            # Check linting results
                            echo "Checking linting results..."
                            if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null; then
                                echo "✅ Linting passed - no critical errors"
                            else
                                echo "❌ Linting failed - critical errors found"
                                exit 1
                            fi
                            
                            # Check security scan results
                            echo "Checking security scan results..."
                            if [ -f bandit-report.json ]; then
                                HIGH_SEVERITY=\$(jq -r '.results[] | select(.issue_severity == "HIGH") | .issue_severity' bandit-report.json | wc -l)
                                if [ "\$HIGH_SEVERITY" -gt 0 ]; then
                                    echo "❌ Security scan failed - high severity issues found"
                                    exit 1
                                else
                                    echo "✅ Security scan passed - no high severity issues"
                                fi
                            fi
                            
                            # Check test results
                            echo "Checking test results..."
                            if [ -f test-results.xml ]; then
                                FAILED_TESTS=\$(grep -c 'failure' test-results.xml || echo "0")
                                if [ "\$FAILED_TESTS" -gt 0 ]; then
                                    echo "❌ Tests failed - \$FAILED_TESTS test(s) failed"
                                    exit 1
                                else
                                    echo "✅ Tests passed - all tests successful"
                                fi
                            fi
                            
                            echo "✅ Automatic code review passed - all quality gates met"
                        """
                    } else {
                        // Manual code review for feature branches
                        echo "Running manual code review for feature branch..."
                        def reviewApproval = input(
                            message: 'Code Review Required - Please review the changes',
                            ok: 'Approve',
                            parameters: [
                                choice(
                                    name: 'REVIEW_STATUS',
                                    choices: ['Approved', 'Needs Changes', 'Request More Info'],
                                    description: 'Code Review Status'
                                )
                            ]
                        )
                        
                        if (reviewApproval != 'Approved') {
                            error "Code review rejected - changes required"
                        }
                    }
                }
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
            steps {
                script {
                    // Check if we're on main branch
                    def currentBranch = env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'unknown'
                    echo "Current branch: ${currentBranch}"
                    
                    if (currentBranch == 'main' || currentBranch == 'origin/main') {
                        echo "Deploying to production from main branch..."
                        input message: 'Deploy to production?', ok: 'Deploy'
                        sh """
                            curl -X POST "${RENDER_DEPLOY_HOOK_PRODUCTION}"
                            echo "Production deployment triggered successfully!"
                        """
                    } else {
                        echo "Skipping production deployment - not on main branch (current: ${currentBranch})"
                    }
                }
            }
        }
        
        stage('Health Check & Auto Rollback') {
            steps {
                script {
                    // Check if we're on main branch
                    def currentBranch = env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'unknown'
                    echo "Current branch: ${currentBranch}"
                    
                    if (currentBranch == 'main' || currentBranch == 'origin/main') {
                        echo "Running health check and auto rollback for main branch..."
                        sh """
                            echo "Waiting for deployment to be ready..."
                            sleep(30)
                            
                            # Get service URL
                            SERVICE_URL=\$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \\
                                "https://api.render.com/v1/services/${RENDER_SERVICE_ID}" | \\
                                jq -r '.service.serviceDetails.url')
                            
                            echo "Service URL: \$SERVICE_URL"
                            
                            # Health check
                            HEALTH_CHECK_PASSED=false
                            for i in {1..10}; do
                                echo "Health check attempt \$i/10..."
                                if curl -f -s --max-time 10 "\$SERVICE_URL/_stcore/health" > /dev/null 2>&1; then
                                    echo "Health check passed!"
                                    HEALTH_CHECK_PASSED=true
                                    break
                                fi
                                echo "Health check failed, retrying in 10 seconds..."
                                sleep 10
                            done
                            
                            if [ "\$HEALTH_CHECK_PASSED" = "false" ]; then
                                echo "Health check failed - initiating rollback..."
                                
                                # Get previous deployment
                                PREVIOUS_DEPLOY_ID=\$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \\
                                    "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys" | \\
                                    jq -r '.deploys[] | select(.status == "live") | .id' | head -2 | tail -1)
                                
                                if [ "\$PREVIOUS_DEPLOY_ID" != "null" ] && [ "\$PREVIOUS_DEPLOY_ID" != "" ]; then
                                    echo "Rolling back to deployment: \$PREVIOUS_DEPLOY_ID"
                                    
                                    # Trigger rollback
                                    curl -s -X POST \\
                                        -H "Authorization: Bearer ${RENDER_API_KEY}" \\
                                        -H "Content-Type: application/json" \\
                                        "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys/\$PREVIOUS_DEPLOY_ID/restore"
                                    
                                    echo "Rollback triggered successfully"
                                else
                                    echo "No previous deployment found for rollback"
                                fi
                            else
                                echo "Service is healthy - no rollback needed"
                            fi
                        """
                    } else {
                        echo "Skipping health check and rollback - not on main branch (current: ${currentBranch})"
                    }
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
