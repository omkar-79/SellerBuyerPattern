# Code Review Guide for Stock Market App

This guide explains how to use the code review functionality integrated into our Jenkins pipeline.

## 🔍 Code Review Features

### 1. **Automated Code Review Stage**
- Generates comprehensive code review reports
- Analyzes code complexity, security, and quality
- Creates detailed markdown reports with metrics
- Archives all review artifacts for later reference

### 2. **Manual Code Review Approval**
- Interactive approval process for non-main branches
- Three approval options: Approved, Needs Changes, Request More Info
- Optional review comments for feedback
- Blocks deployment until approved

### 3. **Pull Request Workflow**
- Separate Jenkinsfile for PR validation (`Jenkinsfile.pr`)
- Runs all quality checks on PR branches
- Generates PR-specific review reports
- Validates changes before merge

## 🚀 How to Use Code Reviews

### For Main Branch (Production)
```bash
# Main pipeline includes automated code review
git push origin main
# Jenkins will run full pipeline with code review stage
```

### For Feature Branches
```bash
# Create feature branch
git checkout -b feature/new-functionality

# Make changes and push
git add .
git commit -m "Add new feature"
git push origin feature/new-functionality

# Create Pull Request
# Jenkins will run PR validation pipeline
```

### For Pull Requests
1. **Create PR** in GitHub/GitLab
2. **Jenkins automatically runs** `Jenkinsfile.pr`
3. **Review the results** in Jenkins console
4. **Check artifacts** for detailed reports
5. **Merge when approved**

## 📊 Code Review Reports

### Generated Reports
- **`code-review/review-report.md`** - Main branch reviews
- **`pr-review/pr-review-report.md`** - Pull request reviews
- **`bandit-report.json`** - Security scan results
- **`htmlcov/index.html`** - Test coverage report

### Report Contents
- 📈 Lines of code analysis
- 🏗️ Function and class counts
- 📦 Import analysis
- 🔒 Security scan summary
- 🧪 Test coverage summary
- 📋 Code quality metrics

## ⚙️ Configuration

### Code Review Settings
Edit `.code-review-config.yml` to customize:
- Required reviewers count
- Quality gate thresholds
- Review checklist items
- File patterns to include/exclude
- Automated check commands

### Quality Gates
- **Linting**: flake8 with complexity and line length limits
- **Security**: bandit and safety vulnerability scans
- **Testing**: pytest with coverage requirements
- **Dependencies**: safety check for known vulnerabilities

## 🔧 Jenkins Pipeline Stages

### Main Pipeline (`Jenkinsfile`)
1. **Checkout** - Get source code
2. **Environment Setup** - Python environment
3. **Code Quality Checks** - Linting and security (parallel)
4. **Code Review** - Generate review reports
5. **Manual Code Review Approval** - Human approval (non-main branches)
6. **Unit Tests** - Run test suite
7. **Build and Package** - Create deployment package
8. **Integration Tests** - Validate functionality
9. **Deploy to Production** - Deploy to Render.com
10. **Rollback Check** - Post-deployment validation

### PR Pipeline (`Jenkinsfile.pr`)
1. **Checkout PR** - Get PR source code
2. **Environment Setup** - Python environment
3. **PR Code Quality Checks** - Linting and security (parallel)
4. **PR Unit Tests** - Run test suite
5. **PR Code Review Report** - Generate PR-specific reports
6. **PR Integration Tests** - Validate functionality

## 📋 Review Checklist

Before approving code, reviewers should check:

- [ ] **Code Style**: Follows PEP 8 guidelines
- [ ] **Documentation**: Functions and classes have docstrings
- [ ] **Security**: No hardcoded secrets or credentials
- [ ] **Error Handling**: Proper exception handling
- [ ] **Testing**: New functionality has unit tests
- [ ] **Performance**: No obvious performance issues
- [ ] **Maintainability**: Code is readable and well-structured
- [ ] **Dependencies**: No unnecessary or vulnerable dependencies

## 🚨 Quality Gates

### Automatic Failures
- **Linting errors** (E9, F63, F7, F82)
- **High severity security issues**
- **Unit test failures**
- **Critical dependency vulnerabilities**

### Warnings (Non-blocking)
- **Code complexity** > 10
- **Line length** > 127 characters
- **Medium severity security issues**
- **Low test coverage** (< 80%)

## 🔄 Workflow Examples

### Feature Development
```bash
# 1. Create feature branch
git checkout -b feature/stock-alerts

# 2. Make changes
# ... code changes ...

# 3. Run local checks
flake8 .
pytest tests/
bandit -r .

# 4. Commit and push
git add .
git commit -m "Add stock price alerts"
git push origin feature/stock-alerts

# 5. Create Pull Request
# Jenkins runs PR pipeline automatically

# 6. Address review feedback
# ... make changes ...

# 7. Merge when approved
```

### Hotfix Process
```bash
# 1. Create hotfix branch
git checkout -b hotfix/security-patch

# 2. Make urgent changes
# ... security fixes ...

# 3. Push and create PR
git push origin hotfix/security-patch

# 4. Fast-track review (if needed)
# Use "Request More Info" for quick approval

# 5. Merge and deploy
```

## 📞 Support

### Common Issues
- **Pipeline fails on linting**: Fix code style issues
- **Security scan fails**: Address vulnerability warnings
- **Tests fail**: Fix failing unit tests
- **Review approval stuck**: Check Jenkins console for input prompts

### Getting Help
- Check Jenkins console output for detailed error messages
- Review generated reports in build artifacts
- Consult `.code-review-config.yml` for configuration details
- Contact DevOps team for pipeline issues

## 🎯 Best Practices

1. **Run local checks** before pushing
2. **Write meaningful commit messages**
3. **Keep PRs small and focused**
4. **Address review feedback promptly**
5. **Test thoroughly** before requesting review
6. **Document complex logic**
7. **Follow security best practices**

---

**Happy Coding! 🚀**
