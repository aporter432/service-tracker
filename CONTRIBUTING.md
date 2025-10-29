# Contributing to ORBCOMM Service Tracker

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Submitting Changes](#submitting-changes)
8. [Review Process](#review-process)

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior:**
- Trolling, insulting/derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct reasonably considered inappropriate

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for containerized development)
- Gmail API credentials (for full functionality)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/service-tracker.git
cd service-tracker

# Add upstream remote
git remote add upstream https://github.com/aporter432/service-tracker.git
```

## Development Setup

### Automated Setup

```bash
# Run setup script
./scripts/setup.sh

# Or manually:
make setup
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-prod.txt

# Create environment file
cp .env.example .env

# Initialize database
python3 -c "from orbcomm_tracker.database import Database; Database().create_tables()"
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

## Making Changes

### Branch Strategy

```bash
# Create feature branch from develop
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### Branch Naming

- Features: `feature/description`
- Bug fixes: `fix/issue-number-description`
- Documentation: `docs/description`
- Refactoring: `refactor/description`
- Tests: `test/description`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): Brief description (max 50 chars)

More detailed explanation (wrap at 72 chars).
Include motivation for change and contrast with previous behavior.

Fixes #123
Refs #456
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(parser): Add support for multi-day incidents

Implemented duration calculation for incidents spanning multiple days.
Updated parser to handle date arithmetic across day boundaries.

Fixes #42
```

```
fix(database): Prevent duplicate notifications

Added unique constraint on reference_number + status combination.
Improved error handling for constraint violations.

Refs #38
```

## Testing

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
pytest tests/test_integration.py -v

# Specific test
pytest tests/test_integration.py::TestDatabaseIntegration::test_notification_lifecycle
```

### Writing Tests

**Unit Tests:**
```python
# tests/test_unit.py
def test_function_name():
    """Test description"""
    result = function_under_test(input)
    assert result == expected_output
```

**Integration Tests:**
```python
# tests/test_integration.py
@pytest.mark.integration
def test_full_workflow():
    """Test complete workflow"""
    # Setup
    # Execute
    # Assert
    # Cleanup
```

### Test Coverage

- Aim for 80%+ coverage on new code
- Critical paths must be tested
- Edge cases should be covered

```bash
# Check coverage
pytest --cov=orbcomm_tracker --cov-report=html
open htmlcov/index.html
```

## Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these tools:

**Black** (auto-formatting):
```bash
make format
```

**isort** (import sorting):
```bash
isort .
```

**Flake8** (linting):
```bash
make lint
```

### Style Rules

- Max line length: 127 characters
- Use double quotes for strings
- Add docstrings to all public functions/classes
- Type hints recommended but not required

**Good:**
```python
def calculate_duration(start: datetime, end: datetime) -> int:
    """
    Calculate duration in minutes between two datetime objects.

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        Duration in minutes
    """
    return int((end - start).total_seconds() / 60)
```

**Bad:**
```python
def calc_dur(s, e):
    return int((e - s).total_seconds() / 60)
```

### Documentation

- Add docstrings to all public APIs
- Update README.md for user-facing changes
- Update DEPLOYMENT.md for deployment changes
- Add inline comments for complex logic

## Submitting Changes

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commits are well-formed
- [ ] Branch is up to date with develop
- [ ] Pre-commit hooks passing

### Pull Request Process

1. **Update your branch:**
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout your-branch
   git rebase develop
   ```

2. **Push to your fork:**
   ```bash
   git push origin your-branch
   ```

3. **Create Pull Request:**
   - Go to GitHub repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #123
Refs #456
```

## Review Process

### What to Expect

1. **Automated Checks** (< 5 minutes)
   - CI/CD pipeline runs
   - Tests must pass
   - Linting must pass
   - Security scans reviewed

2. **Code Review** (1-3 days)
   - Maintainers review code
   - Feedback provided
   - Changes requested if needed

3. **Approval** (after addressing feedback)
   - At least one approval required
   - All conversations resolved

4. **Merge** (after approval)
   - Squash and merge (default)
   - Merge commit (for large features)

### Addressing Feedback

```bash
# Make requested changes
git add .
git commit -m "Address review feedback"
git push origin your-branch
```

**Responding to comments:**
- Acknowledge all feedback
- Ask questions if unclear
- Mark conversations as resolved after addressing

## Development Workflow

### Typical Workflow

1. **Pick an issue:**
   - Check [Issues](https://github.com/aporter432/service-tracker/issues)
   - Comment to claim it
   - Or create new issue for discussion

2. **Create branch:**
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/issue-123-description
   ```

3. **Develop:**
   - Write code
   - Write tests
   - Update docs

4. **Test locally:**
   ```bash
   make ci  # Run full CI pipeline
   ```

5. **Commit:**
   ```bash
   git add .
   git commit -m "feat(scope): Description"
   ```

6. **Push and PR:**
   ```bash
   git push origin feature/issue-123-description
   # Create PR on GitHub
   ```

## Getting Help

### Resources

- [README.md](README.md) - Project overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [CI_CD_GUIDE.md](CI_CD_GUIDE.md) - CI/CD pipeline
- [Issues](https://github.com/aporter432/service-tracker/issues) - Bug reports and features

### Communication

- **Issues:** For bugs and feature requests
- **Pull Requests:** For code contributions
- **Discussions:** For questions and ideas

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Git commit history

Thank you for contributing! 🎉
