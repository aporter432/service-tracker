# Branch Evaluation and Merge Workflow

Automated workflow for evaluating remote branches and conditionally merging them to main.

## Overview

This workflow ensures that only high-quality code gets merged to the main branch by running comprehensive quality checks before allowing any merge operation.

## Quick Start

```bash
# Evaluate and merge a remote branch
./scripts/evaluate_and_merge_branch.sh claude/setup-cicd-pipeline-011CUcD43hHWBzroMafDXaAB
```

## Workflow Steps

### 1. **Fetch Remote Branch**
- Updates local repository with remote changes
- Creates tracking branch if needed

### 2. **Checkout Branch Locally**
- Switches to the feature branch
- Shows commit history and file changes

### 3. **Quality Checks**
The script runs comprehensive quality checks:

#### Pre-commit Hooks
- Trailing whitespace removal
- End-of-file fixing
- YAML validation
- JSON validation
- Black formatting
- isort import sorting
- flake8 linting
- pydocstyle documentation checks

#### Test Suite
- Runs all pytest tests
- Validates test coverage
- Checks for test failures

#### Linting
- flake8 for Python code quality
- Style guide enforcement
- Error detection

### 4. **Evaluation Criteria**

The branch MUST pass all of the following to be merged:
- ✅ All pre-commit hooks pass
- ✅ All tests pass
- ✅ All linting checks pass
- ✅ No flake8 errors

### 5. **Merge Decision**

**If ALL checks pass:**
- Merge to main using `--no-ff` (preserves branch history)
- Create descriptive merge commit
- Optionally push to remote
- Optionally delete feature branch

**If ANY check fails:**
- Stay on feature branch
- Display failure details
- Return to main branch
- Exit with error code

## Usage Examples

### Basic Usage
```bash
# Evaluate and merge a branch
./scripts/evaluate_and_merge_branch.sh feature/new-dashboard
```

### Manual Workflow

If you prefer manual control:

```bash
# 1. Fetch and checkout
git fetch origin
git checkout branch-name

# 2. Run quality checks
pre-commit run --all-files
pytest tests/ -v
flake8 .

# 3. If all pass, merge
git checkout main
git merge --no-ff branch-name
git push origin main
```

## Quality Check Details

### Pre-commit Hooks

The `.pre-commit-config.yaml` defines these checks:

```yaml
- trailing-whitespace    # Remove trailing spaces
- end-of-file-fixer     # Ensure files end with newline
- check-yaml            # Validate YAML syntax
- check-json            # Validate JSON syntax
- check-toml            # Validate TOML syntax
- check-merge-conflicts # Detect merge conflict markers
- debug-statements      # Find debug statements
- mixed-line-ending     # Enforce consistent line endings
- black                 # Python code formatting
- isort                 # Import statement sorting
- flake8                # Python linting
- pydocstyle           # Docstring style checking
```

### Test Suite

Tests must:
- Pass all test cases
- Run without errors
- Complete within timeout
- Maintain or improve coverage

### Linting Standards

Code must:
- Follow PEP 8 style guide
- Have proper docstrings
- Use correct import ordering
- Have no unused imports
- Stay within line length limits (127 chars)
- Use proper exception handling (no bare except)

## Common Issues

### Issue: Pre-commit hooks fail

**Solution**: The script automatically applies fixes for:
- Formatting (black, isort)
- Whitespace issues
- End-of-file fixes

Manual fixes required for:
- Logic errors
- Unused imports
- Bare except clauses
- Line length violations

### Issue: Tests fail

**Solution**:
- Review test output
- Fix failing test logic
- Ensure test environment is correct
- Check for missing dependencies

### Issue: Flake8 errors

**Solution**:
- Fix code quality issues
- Remove unused imports
- Add proper exception handling
- Split long lines
- Add/fix docstrings

## Example: Failed Evaluation

```
==> Step 5: Running pre-commit hooks
✗ Pre-commit hooks failed

Issues found:
- flake8: 45 errors across 15 files
- pydocstyle: 128 warnings

==> Step 8: Quality check evaluation
✗ Quality checks FAILED - branch cannot be merged

Summary:
  - Branch: claude/setup-cicd-pipeline-011CUcD43hHWBzroMafDXaAB
  - Status: ❌ Quality checks failed
  - Action: Branch needs fixes before merging
```

## Example: Successful Merge

```
==> Step 5: Running pre-commit hooks
✓ Pre-commit hooks passed

==> Step 6: Running test suite
✓ All tests passed

==> Step 7: Running flake8 linting
✓ Flake8 linting passed

==> Step 8: Quality check evaluation
✓ All quality checks PASSED

==> Step 9: Merging to main branch
✓ Merged branch to main locally

==> Step 10: Pushing merged changes to remote
✓ Pushed changes to remote

================================================================
✓ Branch evaluation and merge complete!
================================================================
  Branch: feature/new-dashboard
  Status: ✓ Merged to main
  Remote: ✓ Pushed
================================================================
```

## CI/CD Integration

This workflow integrates with the CI/CD pipeline:

1. **Local Pre-merge Check**: Run this script before creating PR
2. **CI Pipeline**: GitHub Actions runs same checks on PR
3. **Manual Review**: Code review by team members
4. **Automated Merge**: Script automates local merge after approval

## Best Practices

### Before Running Script
- Commit all local changes
- Ensure you're on a clean main branch
- Have pre-commit installed: `pip install pre-commit`
- Have pytest installed: `pip install pytest`

### After Successful Merge
- Delete feature branch (script will prompt)
- Notify team members
- Update project documentation if needed
- Close related issues

### When Quality Checks Fail
- Review all error messages
- Fix issues on the feature branch
- Push fixes to remote
- Re-run evaluation script

## Troubleshooting

### Script exits immediately
**Cause**: Not on main branch or uncommitted changes
**Fix**:
```bash
git stash
git checkout main
./scripts/evaluate_and_merge_branch.sh branch-name
```

### Merge conflicts
**Cause**: Divergent main and feature branches
**Fix**:
```bash
git checkout feature-branch
git rebase main
# Resolve conflicts
./scripts/evaluate_and_merge_branch.sh feature-branch
```

### Pre-commit not found
**Cause**: pre-commit not installed
**Fix**:
```bash
pip install pre-commit
pre-commit install
```

## Script Configuration

Edit `scripts/evaluate_and_merge_branch.sh` to customize:

```bash
# Main branch name (default: main)
MAIN_BRANCH="main"

# Quality check failure flag
QUALITY_CHECK_FAILED=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
```

## Integration with Claude Code

This workflow can be triggered via:

```bash
# From Claude Code
/sc:git "evaluate and merge branch claude/feature-name"

# Direct script execution
./scripts/evaluate_and_merge_branch.sh claude/feature-name
```

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [CI_CD_GUIDE.md](../CI_CD_GUIDE.md) - CI/CD pipeline details
- [.pre-commit-config.yaml](../.pre-commit-config.yaml) - Pre-commit configuration
- [pytest.ini](../pytest.ini) - Test configuration

## Summary

This automated workflow ensures:
- ✅ Code quality standards are met
- ✅ All tests pass before merge
- ✅ Formatting is consistent
- ✅ No regressions are introduced
- ✅ Main branch stays stable
- ✅ Merge history is preserved

**Result**: High-quality, production-ready code in main branch.
