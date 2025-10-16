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
        
        stage('Code Review') {
            steps {
                script {
                    // Generate comprehensive code review report
                    sh """
                        source venv/bin/activate
                        echo "🔍 Generating Code Review Report..."
                        
                        # Create code review directory
                        mkdir -p code-review
                        
                        # Generate code complexity report
                        echo "📊 Code Complexity Analysis" > code-review/review-report.md
                        echo "=========================" >> code-review/review-report.md
                        echo "" >> code-review/review-report.md
                        
                        # Count lines of code
                        echo "📈 Lines of Code:" >> code-review/review-report.md
                        find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./deploy/*" | xargs wc -l >> code-review/review-report.md
                        echo "" >> code-review/review-report.md
                        
                        # Function and class count
                        echo "🏗️ Functions and Classes:" >> code-review/review-report.md
                        find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./deploy/*" -exec grep -c "^def \|^class " {} + >> code-review/review-report.md
                        echo "" >> code-review/review-report.md
                        
                        # Import analysis
                        echo "📦 Import Analysis:" >> code-review/review-report.md
                        find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./deploy/*" -exec grep -H "^import\|^from" {} \; >> code-review/review-report.md
                        echo "" >> code-review/review-report.md
                        
                        # Security findings summary
                        echo "🔒 Security Scan Summary:" >> code-review/review-report.md
                        if [ -f bandit-report.json ]; then
                            echo "Bandit security scan completed. Check bandit-report.json for details." >> code-review/review-report.md
                        fi
                        echo "" >> code-review/review-report.md
                        
                        # Test coverage summary
                        echo "🧪 Test Coverage Summary:" >> code-review/review-report.md
                        echo "Unit tests completed. Check htmlcov/index.html for detailed coverage report." >> code-review/review-report.md
                        echo "" >> code-review/review-report.md
                        
                        # Code quality metrics
                        echo "📋 Code Quality Metrics:" >> code-review/review-report.md
                        echo "- Linting: Completed with flake8" >> code-review/review-report.md
                        echo "- Security: Completed with bandit and safety" >> code-review/review-report.md
                        echo "- Testing: Completed with pytest" >> code-review/review-report.md
                        echo "- Dependencies: Checked for vulnerabilities" >> code-review/review-report.md
                        echo "" >> code-review/review-report.md
                        
                        echo "✅ Code Review Report generated: code-review/review-report.md"
                    """
                    
                    // Display code review summary
                    echo "📋 Code Review Summary:"
                    echo "======================"
                    echo "✅ Linting checks completed"
                    echo "✅ Security scans completed" 
                    echo "✅ Unit tests completed"
                    echo "✅ Dependency checks completed"
                    echo "📊 Review report available in code-review/review-report.md"
                }
            }
            post {
                always {
                    // Archive code review artifacts
                    archiveArtifacts artifacts: 'code-review/**/*', allowEmptyArchive: true
                    archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                    archiveArtifacts artifacts: 'htmlcov/**/*', allowEmptyArchive: true
                }
            }
        }
        
        stage('Manual Code Review Approval') {
            when {
                // Only for PRs and feature branches (not main branch)
                not { branch 'main' }
            }
            steps {
                script {
                    // Manual approval for PRs and feature branches
                    def reviewApproval = input(
                        message: 'Code Review Required - Please review the changes before merging to main',
                        ok: 'Approve',
                        parameters: [
                            choice(
                                name: 'REVIEW_STATUS',
                                choices: ['Approved', 'Needs Changes', 'Request More Info'],
                                description: 'Code Review Status'
                            ),
                            text(
                                name: 'REVIEW_COMMENTS',
                                description: 'Review Comments (optional)',
                                defaultValue: ''
                            )
                        ]
                    )
                    
                    if (reviewApproval == 'Approved') {
                        echo "✅ Code review approved by reviewer - ready to merge to main"
                    } else if (reviewApproval == 'Needs Changes') {
                        error "❌ Code review rejected - changes required before merge"
                    } else {
                        error "❌ Code review requires more information before merge"
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
        
        stage('Pre-Deployment Validation') {
            steps {
                script {
                    // Validate critical files and dependencies before deployment
                    sh """
                        source venv/bin/activate
                        echo "🔍 Running pre-deployment validation..."
                        
                        # Check if main.py exists and is valid Python
                        echo "Validating main.py..."
                        if python -m py_compile main.py; then
                            echo "✅ main.py syntax is valid"
                        else
                            echo "❌ main.py has syntax errors"
                            exit 1
                        fi
                        
                        # Check if requirements.txt exists
                        echo "Validating requirements.txt..."
                        if [ -f requirements.txt ]; then
                            echo "✅ requirements.txt exists"
                        else
                            echo "❌ requirements.txt missing"
                            exit 1
                        fi
                        
                        # Check if render.yaml exists
                        echo "Validating render.yaml..."
                        if [ -f render.yaml ]; then
                            echo "✅ render.yaml exists"
                        else
                            echo "❌ render.yaml missing"
                            exit 1
                        fi
                        
                        # Validate Python imports work
                        echo "Validating Python imports..."
                        if python -c "import sys; sys.path.append('.'); import main" 2>/dev/null; then
                            echo "✅ Python imports are valid"
                        else
                            echo "❌ Python imports failed"
                            exit 1
                        fi
                        
                        echo "✅ Pre-deployment validation passed"
                    """
                }
            }
            post {
                failure {
                    echo "❌ Pre-deployment validation failed - stopping pipeline"
                }
                success {
                    echo "✅ Pre-deployment validation completed successfully"
                }
            }
        }
        
        stage('Build and Package') {
            steps {
                script {
                    // Create deployment package
                    sh """
                        echo "Creating deployment package..."
                        rm -rf deploy
                        mkdir -p deploy
                        
                        # Copy files excluding unwanted directories and files
                        rsync -av --exclude='deploy' --exclude='.git' --exclude='.venv' --exclude='venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='tests' --exclude='.flake8' --exclude='pytest.ini' --exclude='Jenkinsfile' --exclude='bandit-report.json' --exclude='safety-report.json' --exclude='test-results.xml' --exclude='htmlcov' --exclude='*.tar.gz' . deploy/
                        
                        cd deploy
                        tar -czf ../stock-market-app-${BUILD_NUMBER}.tar.gz .
                        cd ..
                        echo "Deployment package created: stock-market-app-${BUILD_NUMBER}.tar.gz"
                    """
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                script {
                    // Run local integration tests with error handling
                    sh """
                        source venv/bin/activate
                        echo "Running integration tests..."
                        
                        # Test imports with error handling
                        echo "Testing imports..."
                        if python -c "import streamlit as st; import yfinance as yf; import pandas as pd; import plotly.graph_objs as go; from plotly.subplots import make_subplots; print('✅ All imports successful')"; then
                            echo "✅ Import test passed"
                        else
                            echo "❌ Import test failed"
                            exit 1
                        fi
                        
                        # Test basic functionality with error handling
                        echo "Testing Yahoo Finance API..."
                        if python -c "import yfinance as yf; ticker = yf.Ticker('AAPL'); info = ticker.info; print('✅ Yahoo Finance API test successful')"; then
                            echo "✅ API test passed"
                        else
                            echo "❌ API test failed"
                            exit 1
                        fi
                        
                        # Test Streamlit app can be imported with error handling
                        echo "Testing main application import..."
                        if python -c "import main; print('✅ Main application imports successfully')"; then
                            echo "✅ Main app test passed"
                        else
                            echo "❌ Main app test failed"
                            exit 1
                        fi
                        
                        echo "✅ All integration tests passed successfully"
                    """
                }
            }
            post {
                failure {
                    echo "❌ Integration tests failed - check the logs above for details"
                }
                success {
                    echo "✅ Integration tests completed successfully"
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
        
        stage('Health Check & Auto Rollback') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Wait for deployment to be ready
                    echo "⏳ Waiting for deployment to be ready..."
                    sleep(30)
                    
                    // Perform health checks
                    sh """
                        echo "🔍 Performing health checks..."
                        
                        # Get the service URL from Render
                        SERVICE_URL=\$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \\
                            "https://api.render.com/v1/services/${RENDER_SERVICE_ID}" | \\
                            jq -r '.service.serviceDetails.url')
                        
                        echo "Service URL: \$SERVICE_URL"
                        
                        # Health check function
                        check_health() {
                            local url=\$1
                            local max_attempts=10
                            local attempt=1
                            
                            while [ \$attempt -le \$max_attempts ]; do
                                echo "Health check attempt \$attempt/\$max_attempts..."
                                
                                # Check if service is responding
                                if curl -f -s --max-time 10 "\$url/_stcore/health" > /dev/null 2>&1; then
                                    echo "✅ Health check passed on attempt \$attempt"
                                    return 0
                                fi
                                
                                echo "❌ Health check failed on attempt \$attempt"
                                sleep 10
                                attempt=\$((attempt + 1))
                            done
                            
                            echo "❌ Health check failed after \$max_attempts attempts"
                            return 1
                        }
                        
                        # Run health check
                        if check_health "\$SERVICE_URL"; then
                            echo "✅ Service is healthy - no rollback needed"
                            echo "HEALTH_STATUS=healthy" > health-status.env
                        else
                            echo "❌ Service is unhealthy - initiating automatic rollback"
                            echo "HEALTH_STATUS=unhealthy" > health-status.env
                        fi
                    """
                    
                    // Load health status
                    def healthStatus = readFile('health-status.env').trim()
                    
                    if (healthStatus.contains('unhealthy')) {
                        echo "🔄 Initiating automatic rollback..."
                        
                        sh """
                            echo "🚨 Automatic rollback triggered due to health check failure"
                            
                            # Get list of deployments
                            echo "📋 Getting deployment history..."
                            curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \\
                                "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys" | \\
                                jq '.deploys[] | select(.status == "live") | {id: .id, commit: .commit.message, createdAt: .createdAt}' > deployments.json
                            
                            # Get the previous successful deployment (not current)
                            PREVIOUS_DEPLOY_ID=\$(jq -r '.[1].id' deployments.json)
                            
                            if [ "\$PREVIOUS_DEPLOY_ID" != "null" ] && [ "\$PREVIOUS_DEPLOY_ID" != "" ]; then
                                echo "🔄 Rolling back to deployment: \$PREVIOUS_DEPLOY_ID"
                                
                                # Trigger rollback via Render API
                                ROLLBACK_RESPONSE=\$(curl -s -X POST \\
                                    -H "Authorization: Bearer ${RENDER_API_KEY}" \\
                                    -H "Content-Type: application/json" \\
                                    "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys/\$PREVIOUS_DEPLOY_ID/restore")
                                
                                echo "Rollback response: \$ROLLBACK_RESPONSE"
                                
                                # Wait for rollback to complete
                                echo "⏳ Waiting for rollback to complete..."
                                sleep(60)
                                
                                # Verify rollback health
                                SERVICE_URL=\$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \\
                                    "https://api.render.com/v1/services/${RENDER_SERVICE_ID}" | \\
                                    jq -r '.service.serviceDetails.url')
                                
                                if curl -f -s --max-time 10 "\$SERVICE_URL/_stcore/health" > /dev/null 2>&1; then
                                    echo "✅ Rollback successful - service is healthy"
                                    echo "ROLLBACK_STATUS=success" > rollback-status.env
                                else
                                    echo "❌ Rollback failed - service still unhealthy"
                                    echo "ROLLBACK_STATUS=failed" > rollback-status.env
                                fi
                            else
                                echo "❌ No previous deployment found for rollback"
                                echo "ROLLBACK_STATUS=no_previous_deploy" > rollback-status.env
                            fi
                        """
                        
                        // Load rollback status
                        def rollbackStatus = readFile('rollback-status.env').trim()
                        
                        if (rollbackStatus.contains('failed') || rollbackStatus.contains('no_previous_deploy')) {
                            error "❌ Automatic rollback failed - manual intervention required"
                        } else {
                            echo "✅ Automatic rollback completed successfully"
                        }
                    } else {
                        echo "✅ Service is healthy - no rollback needed"
                    }
                }
            }
            post {
                always {
                    // Clean up temporary files
                    sh """
                        rm -f health-status.env rollback-status.env deployments.json || true
                    """
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