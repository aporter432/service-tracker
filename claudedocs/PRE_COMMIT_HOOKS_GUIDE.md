# Pre-Commit Hooks Guide

Complete guide to the pre-commit hooks configured for this project, including which hooks auto-fix issues.

## Installation

```bash
pip install pre-commit
pre-commit install
```

## Running Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Run specific hook
pre-commit run black --all-files
```

## Hooks Configuration Summary

### ✅ Auto-Fix Hooks (Modify Files Automatically)

These hooks will **automatically fix issues** when detected:

| Hook | What It Fixes | Example |
|------|---------------|---------|
| **trailing-whitespace** | Removes trailing spaces/tabs at line ends | `foo = bar   ` → `foo = bar` |
| **end-of-file-fixer** | Ensures files end with newline | `last line` → `last line\n` |
| **mixed-line-ending** | Standardizes line endings (LF) | `\r\n` → `\n` |
| **black** | Python code formatting | Entire file reformatted to Black style |
| **isort** | Python import statement sorting | Imports reordered alphabetically by category |

**Behavior**: When these hooks run and make changes:
1. Files are modified in place
2. You must stage the changes: `git add .`
3. Re-run the hooks to verify: `pre-commit run --all-files`

### ❌ Check-Only Hooks (Report Issues, Manual Fix Required)

These hooks **only detect issues** - you must fix them manually:

| Hook | What It Checks | Common Issues |
|------|----------------|---------------|
| **check-yaml** | YAML syntax validation | Invalid YAML structure, indentation errors |
| **check-json** | JSON syntax validation | Missing commas, trailing commas, quotes |
| **check-toml** | TOML syntax validation | Invalid TOML structure |
| **check-added-large-files** | File size limit (1MB) | Accidentally committed large files |
| **check-merge-conflict** | Merge conflict markers | `<<<<<<`, `======`, `>>>>>>` in code |
| **debug-statements** | Python debug statements | `import pdb`, `pdb.set_trace()`, `breakpoint()` |
| **flake8** | Python linting | See [Flake8 Issues](#flake8-issues) below |
| **bandit** | Security vulnerabilities | Hardcoded passwords, insecure functions |

**Behavior**: When these hooks fail:
1. Error messages show what needs fixing
2. You must manually fix the issues
3. Stage fixes: `git add .`
4. Re-run hooks to verify: `pre-commit run --all-files`

## Detailed Hook Descriptions

### 1. trailing-whitespace ✅ Auto-Fix
**Purpose**: Remove unnecessary whitespace at end of lines

**Auto-fixes**:
```python
# Before
def hello():
    return "world"

# After
def hello():
    return "world"
```

**Configuration**: Default (all files)

---

### 2. end-of-file-fixer ✅ Auto-Fix
**Purpose**: Ensure files end with single newline

**Auto-fixes**:
```python
# Before (no newline at end)
def hello():
    return "world"
# After (newline added)
def hello():
    return "world"

```

**Configuration**: Default (all files)

---

### 3. check-yaml ❌ Check Only
**Purpose**: Validate YAML syntax

**Example failures**:
```yaml
# Invalid indentation
key:
value: wrong

# Fixed
key:
  value: correct
```

**Configuration**:
- Excludes: `kubernetes/` (multi-document YAML files)

---

### 4. check-added-large-files ❌ Check Only
**Purpose**: Prevent committing large files (>1MB)

**Common triggers**:
- Database files (*.db, *.sqlite)
- Log files (*.log)
- Binary files (*.bin, *.exe)
- Large media files

**Fix**: Use `.gitignore` or Git LFS for large files

**Configuration**: `--maxkb=1000` (1MB limit)

---

### 5. check-json ❌ Check Only
**Purpose**: Validate JSON syntax

**Example failures**:
```json
// Invalid trailing comma
{
  "key": "value",
}

// Fixed
{
  "key": "value"
}
```

---

### 6. check-merge-conflict ❌ Check Only
**Purpose**: Detect merge conflict markers

**Detects**:
```python
<<<<<<< HEAD
def old_function():
=======
def new_function():
>>>>>>> feature-branch
```

**Fix**: Resolve merge conflicts manually

---

### 7. debug-statements ❌ Check Only
**Purpose**: Find debug statements left in code

**Detects**:
```python
import pdb
pdb.set_trace()
breakpoint()
import ipdb
```

**Fix**: Remove debug statements before committing

---

### 8. mixed-line-ending ✅ Auto-Fix
**Purpose**: Standardize line endings to LF (\n)

**Auto-fixes**:
- Windows CRLF (`\r\n`) → Unix LF (`\n`)
- Old Mac CR (`\r`) → Unix LF (`\n`)

**Configuration**: Enforces LF for consistency

---

### 9. black ✅ Auto-Fix
**Purpose**: Automatic Python code formatting

**Auto-fixes**:
- Line length (88 chars by default)
- Quote style (double quotes)
- Spacing around operators
- Function/class spacing
- Import formatting

**Example**:
```python
# Before
def hello(x,y,z):
    return x+y+z

# After
def hello(x, y, z):
    return x + y + z
```

**Configuration**:
- Version: 23.12.1 (pinned for consistency)
- Python: python3

---

### 10. isort ✅ Auto-Fix
**Purpose**: Sort Python import statements

**Auto-fixes**:
```python
# Before (unsorted)
from os import path
import sys
from datetime import datetime
import os

# After (sorted by category, alphabetically)
import os
import sys
from datetime import datetime
from os import path
```

**Configuration**:
- Profile: `black` (compatible with Black formatting)
- Categories: stdlib → third-party → local

---

### 11. flake8 ❌ Check Only
**Purpose**: Python linting and style checking

**Configuration**:
- Max line length: 127 characters
- Ignored rules:
  - `E203`: Whitespace before ':' (Black compatibility)
  - `W503`: Line break before binary operator (Black compatibility)

**Common issues detected**:
See [Flake8 Issues](#flake8-issues) section below

---

### 12. bandit ❌ Check Only
**Purpose**: Security vulnerability scanning

**Scans**: `orbcomm_tracker/` directory
**Excludes**: `tests/` (test code may use insecure patterns)

**Common detections**:
- Hardcoded passwords
- Use of `eval()` or `exec()`
- Weak cryptographic functions
- SQL injection vulnerabilities
- Shell injection risks

## Flake8 Issues

Common flake8 errors that require manual fixing:

### F401: Module imported but unused
```python
# Error
import os  # F401: 'os' imported but unused

# Fix: Remove unused import or use it
import os
os.path.exists('file.txt')
```

### F541: f-string missing placeholders
```python
# Error
message = f"Hello world"  # F541: no placeholders

# Fix: Remove f-string prefix or add placeholder
message = "Hello world"
# OR
name = "World"
message = f"Hello {name}"
```

### E501: Line too long
```python
# Error
very_long_line = "This is an extremely long line that exceeds the maximum allowed length of 127 characters and should be split"

# Fix: Split into multiple lines
very_long_line = (
    "This is an extremely long line that exceeds "
    "the maximum allowed length of 127 characters"
)
```

### E402: Module level import not at top of file
```python
# Error
print("Starting")
import os  # E402: should be at top

# Fix: Move imports to top
import os

print("Starting")
```

### E722: Bare except clause
```python
# Error
try:
    risky_operation()
except:  # E722: bare except
    pass

# Fix: Specify exception type
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
```

### E203, W503: Ignored for Black compatibility
These are automatically ignored because Black formatter may produce code that violates these rules.

## Workflow Integration

### Pre-Commit (Automatic)
When you run `git commit`, hooks run automatically:

```bash
git add file.py
git commit -m "Add feature"

# Hooks run automatically
# If auto-fix hooks modify files:
git add file.py  # Stage the fixes
git commit -m "Add feature"  # Commit again
```

### Manual Run (Testing)
Test hooks before committing:

```bash
# All hooks on all files
pre-commit run --all-files

# All hooks on staged files
pre-commit run

# Specific hook
pre-commit run black
pre-commit run flake8
```

### CI/CD Pipeline
Hooks also run in GitHub Actions:

```yaml
# .github/workflows/ci.yml
- name: Run pre-commit hooks
  run: pre-commit run --all-files
```

## Bypassing Hooks (Not Recommended)

**Only use in emergencies**:

```bash
# Skip all hooks for one commit
git commit --no-verify -m "Emergency fix"

# Skip specific hook
SKIP=flake8 git commit -m "WIP: incomplete feature"
```

**Warning**: Bypassing hooks can introduce:
- Formatting inconsistencies
- Linting errors
- Security vulnerabilities
- Build failures in CI/CD

## Troubleshooting

### Issue: Hooks not running automatically
**Cause**: Pre-commit not installed
**Fix**:
```bash
pre-commit install
```

### Issue: Hooks fail on large repository
**Cause**: Many files need auto-fixing
**Fix**:
```bash
# Run once to fix all files
pre-commit run --all-files

# Stage and commit fixes
git add .
git commit -m "fix: Apply pre-commit formatting to entire codebase"
```

### Issue: Black and flake8 conflict
**Cause**: Flake8 rules incompatible with Black
**Fix**: Already configured! E203 and W503 are ignored.

### Issue: YAML check fails on kubernetes/
**Cause**: Multi-document YAML files
**Fix**: Already configured! kubernetes/ is excluded.

### Issue: Auto-fix loops (keeps modifying files)
**Cause**: Conflicting formatters or configuration
**Fix**:
1. Check for conflicting `.editorconfig` or IDE settings
2. Ensure Black and isort use compatible settings
3. Already configured! isort uses `--profile black`

## Best Practices

### 1. Run Before Committing
```bash
pre-commit run --all-files
git add .
git commit -m "Your message"
```

### 2. Update Hooks Regularly
```bash
pre-commit autoupdate
```

### 3. Fix Auto-Fix Issues First
Let auto-fix hooks clean up formatting, then fix check-only issues.

### 4. Stage Auto-Fixes
After auto-fix hooks run:
```bash
git add .
pre-commit run --all-files  # Verify fixes
```

### 5. Read Error Messages
Check-only hooks provide clear guidance on what needs fixing.

## Summary Table

| Hook | Auto-Fix | Speed | Impact |
|------|----------|-------|--------|
| trailing-whitespace | ✅ | Fast | Low |
| end-of-file-fixer | ✅ | Fast | Low |
| check-yaml | ❌ | Fast | Medium |
| check-added-large-files | ❌ | Fast | High |
| check-json | ❌ | Fast | Medium |
| check-toml | ❌ | Fast | Medium |
| check-merge-conflict | ❌ | Fast | High |
| debug-statements | ❌ | Fast | Medium |
| mixed-line-ending | ✅ | Fast | Low |
| **black** | ✅ | Medium | **High** |
| **isort** | ✅ | Fast | Medium |
| **flake8** | ❌ | Medium | **High** |
| bandit | ❌ | Slow | High |

**Legend**:
- **Auto-Fix**: Hook modifies files automatically
- **Speed**: How fast the hook runs
- **Impact**: How much the hook affects code quality

## Related Documentation

- [.pre-commit-config.yaml](../.pre-commit-config.yaml) - Hook configuration
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [CI_CD_GUIDE.md](../CI_CD_GUIDE.md) - CI/CD pipeline integration
- [BRANCH_EVALUATION_WORKFLOW.md](BRANCH_EVALUATION_WORKFLOW.md) - Branch merge workflow

## Quick Reference

**Auto-Fix Hooks (5 total)**:
1. trailing-whitespace
2. end-of-file-fixer
3. mixed-line-ending
4. **black** (most impactful)
5. **isort**

**Check-Only Hooks (8 total)**:
1. check-yaml
2. check-added-large-files
3. check-json
4. check-toml
5. check-merge-conflict
6. debug-statements
7. **flake8** (most impactful)
8. bandit

**Result**: 5 auto-fix, 8 check-only = 13 total hooks configured
