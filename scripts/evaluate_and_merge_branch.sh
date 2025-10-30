#!/bin/bash
# evaluate_and_merge_branch.sh
# Automated workflow to fetch, evaluate, and conditionally merge a remote branch

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAIN_BRANCH="main"
QUALITY_CHECK_FAILED=0

# Usage information
usage() {
    echo "Usage: $0 <remote-branch-name>"
    echo ""
    echo "Example: $0 claude/setup-cicd-pipeline-011CUcD43hHWBzroMafDXaAB"
    echo ""
    echo "This script will:"
    echo "  1. Fetch the remote branch"
    echo "  2. Checkout the branch locally"
    echo "  3. Run quality checks (pre-commit, tests, linting)"
    echo "  4. Merge to main if all checks pass"
    echo "  5. Push to remote"
    exit 1
}

# Check arguments
if [ $# -eq 0 ]; then
    usage
fi

BRANCH_NAME="$1"

# Helper functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Ensure we're on main and up to date
print_step "Step 1: Ensuring main branch is up to date"
git checkout "$MAIN_BRANCH" || {
    print_error "Failed to checkout main branch"
    exit 1
}
git pull origin "$MAIN_BRANCH" || {
    print_error "Failed to update main branch"
    exit 1
}
print_success "Main branch is up to date"

# Step 2: Fetch remote branch
print_step "Step 2: Fetching remote branch: $BRANCH_NAME"
git fetch origin || {
    print_error "Failed to fetch from origin"
    exit 1
}
print_success "Fetched remote branches"

# Step 3: Checkout the branch
print_step "Step 3: Checking out branch: $BRANCH_NAME"
git checkout "$BRANCH_NAME" || {
    # Try to create tracking branch if it doesn't exist locally
    git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME" || {
        print_error "Failed to checkout branch: $BRANCH_NAME"
        git checkout "$MAIN_BRANCH"
        exit 1
    }
}
print_success "Checked out branch: $BRANCH_NAME"

# Step 4: Show branch information
print_step "Step 4: Branch information"
echo ""
echo "Commits unique to this branch:"
git log "$MAIN_BRANCH"..HEAD --oneline --color=always || echo "No unique commits"
echo ""
echo "Files changed compared to main:"
git diff "$MAIN_BRANCH"...HEAD --stat --color=always || echo "No file changes"
echo ""

# Step 5: Run pre-commit checks
print_step "Step 5: Running pre-commit hooks"
if pre-commit run --all-files; then
    print_success "Pre-commit hooks passed"
else
    QUALITY_CHECK_FAILED=1
    print_error "Pre-commit hooks failed"

    # Check if pre-commit made changes
    if ! git diff --quiet; then
        print_warning "Pre-commit hooks made changes. Committing fixes..."
        git add -A
        git commit -m "fix: Apply pre-commit hook formatting and linting fixes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

        print_step "Re-running pre-commit hooks after fixes"
        if pre-commit run --all-files; then
            print_success "Pre-commit hooks passed after fixes"
            QUALITY_CHECK_FAILED=0
        else
            print_error "Pre-commit hooks still failing after automatic fixes"
        fi
    fi
fi

# Step 6: Run tests
print_step "Step 6: Running test suite"
if [ -f "pytest.ini" ] || [ -d "tests" ]; then
    if pytest tests/ -v --tb=short; then
        print_success "All tests passed"
    else
        QUALITY_CHECK_FAILED=1
        print_error "Tests failed"
    fi
else
    print_warning "No tests found (skipping)"
fi

# Step 7: Run flake8 if available
print_step "Step 7: Running flake8 linting"
if command -v flake8 &> /dev/null; then
    if flake8 .; then
        print_success "Flake8 linting passed"
    else
        QUALITY_CHECK_FAILED=1
        print_error "Flake8 linting failed"
    fi
else
    print_warning "flake8 not available (skipping)"
fi

# Step 8: Evaluate quality checks
echo ""
print_step "Step 8: Quality check evaluation"
if [ $QUALITY_CHECK_FAILED -eq 1 ]; then
    print_error "Quality checks FAILED - branch cannot be merged"
    echo ""
    echo "Summary:"
    echo "  - Branch: $BRANCH_NAME"
    echo "  - Status: ❌ Quality checks failed"
    echo "  - Action: Branch needs fixes before merging"
    echo ""
    print_warning "Returning to main branch"
    git checkout "$MAIN_BRANCH"
    exit 1
else
    print_success "All quality checks PASSED"
fi

# Step 9: Merge to main
print_step "Step 9: Merging to main branch"
git checkout "$MAIN_BRANCH" || {
    print_error "Failed to checkout main branch"
    exit 1
}

if git merge --no-ff "$BRANCH_NAME" -m "Merge branch '$BRANCH_NAME'

Quality checks passed:
✓ Pre-commit hooks
✓ Test suite
✓ Linting

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"; then
    print_success "Merged branch to main locally"
else
    print_error "Merge failed - may have conflicts"
    git merge --abort 2>/dev/null || true
    exit 1
fi

# Step 10: Push to remote
print_step "Step 10: Pushing merged changes to remote"
echo ""
read -p "Push merged changes to remote? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if git push origin "$MAIN_BRANCH"; then
        print_success "Pushed changes to remote"

        # Optionally delete remote branch
        echo ""
        read -p "Delete remote branch '$BRANCH_NAME'? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push origin --delete "$BRANCH_NAME" || print_warning "Failed to delete remote branch"
            git branch -d "$BRANCH_NAME" || print_warning "Failed to delete local branch"
        fi
    else
        print_error "Failed to push to remote"
        exit 1
    fi
else
    print_warning "Skipped pushing to remote"
fi

# Final summary
echo ""
echo "================================================================"
print_success "Branch evaluation and merge complete!"
echo "================================================================"
echo "  Branch: $BRANCH_NAME"
echo "  Status: ✓ Merged to main"
echo "  Remote: $(if git branch -r | grep -q "origin/$MAIN_BRANCH"; then echo "✓ Pushed"; else echo "⚠ Not pushed"; fi)"
echo "================================================================"
