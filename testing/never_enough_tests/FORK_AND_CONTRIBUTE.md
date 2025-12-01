# Contributing to the pytest Repository

This guide explains how to properly set up your fork and create a pull request to contribute the Never Enough Tests suite to the pytest repository.

## Prerequisites

- Git installed on your system
- GitHub account
- Python 3.8+ installed
- C++ compiler (g++ with C++17 support)

## Step-by-Step Contribution Guide

### 1. Fork the pytest Repository

1. Go to https://github.com/pytest-dev/pytest
2. Click the "Fork" button in the top-right corner
3. This creates your own copy at `https://github.com/YOUR_USERNAME/pytest`

### 2. Set Up Your Local Repository

```bash
# Clone your fork (replace YOUR_USERNAME with your GitHub username)
git clone https://github.com/YOUR_USERNAME/pytest.git
cd pytest

# Add the original pytest repo as "upstream"
git remote add upstream https://github.com/pytest-dev/pytest.git

# Verify remotes
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/pytest.git (fetch)
# origin    https://github.com/YOUR_USERNAME/pytest.git (push)
# upstream  https://github.com/pytest-dev/pytest.git (fetch)
# upstream  https://github.com/pytest-dev/pytest.git (push)
```

### 3. Create Your Feature Branch

```bash
# Make sure you're on main
git checkout main

# Pull latest changes from upstream
git fetch upstream
git merge upstream/main

# Create your feature branch
git checkout -b feature/never-enough-tests-stress-suite
```

### 4. Copy the Never Enough Tests Suite

If you developed the suite elsewhere, copy it to the pytest testing directory:

```bash
# From your development location
cp -r /path/to/never_enough_tests testing/

# Or if you're starting fresh, the files are already in the repo
```

### 5. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install pytest in development mode
pip install -e .

# Install required plugins
pip install pytest-xdist pytest-random-order pytest-timeout pytest-asyncio

# Build C++ components
cd testing/never_enough_tests/cpp_components
make
cd ../../..
```

### 6. Test Your Changes

```bash
# Run the full test suite
./venv/bin/pytest testing/never_enough_tests/ -n 4 -v

# Verify all tests pass
# Expected: 1,626+ passed in ~18 seconds

# Run specific test categories
./venv/bin/pytest testing/never_enough_tests/ -k "parametrize" -v
./venv/bin/pytest testing/never_enough_tests/ -k "cpp_boundary" -v
```

### 7. Commit Your Changes

```bash
# Stage all files
git add testing/never_enough_tests/

# Create a descriptive commit
git commit -m "Add Never Enough Tests: Comprehensive stress testing suite

This contribution adds a comprehensive stress testing suite for pytest that
pushes the boundaries of pytest's capabilities and validates its behavior
under extreme conditions.

Features:
- 1,660+ test cases covering edge cases and stress scenarios
- Parametrization explosion testing (1,000 tests from single function)
- Cross-language integration tests (Python ↔ C++)
- Deep fixture chain validation (5+ levels)
- Chaos testing with randomization
- Performance benchmarking tools

Test Results:
- Successfully executed 1,626 tests in 17.82s with 4 parallel workers
- Validated against pytest 9.1.0.dev107+g8fb7815f1
- Found and fixed C++ buffer boundary bug during development

Benefits:
- Validates pytest handles extreme parametrization efficiently
- Tests cross-language subprocess integration patterns
- Provides regression testing for performance at scale
- Demonstrates best practices for large test suites"
```

### 8. Push to Your Fork

```bash
# Push your feature branch to your fork
git push origin feature/never-enough-tests-stress-suite

# If this is the first push, Git will provide the exact command
```

### 9. Create a Pull Request

1. Go to your fork on GitHub: `https://github.com/YOUR_USERNAME/pytest`
2. You'll see a banner suggesting to create a PR for your recently pushed branch
3. Click "Compare & pull request"
4. Fill in the PR template:
   - **Title**: "Add Never Enough Tests: Comprehensive stress testing suite"
   - **Description**: Use the commit message as a base, add any additional context
   - **Labels**: Add appropriate labels (enhancement, testing, etc.)
5. Click "Create pull request"

### 10. Address Review Feedback

```bash
# After code review, make changes
git add <modified-files>
git commit -m "Address review feedback: <description>"
git push origin feature/never-enough-tests-stress-suite

# The PR will automatically update
```

### 11. Keep Your Branch Up to Date

If upstream changes while your PR is being reviewed:

```bash
# Fetch latest from upstream
git fetch upstream

# Rebase your branch on top of latest main
git rebase upstream/main

# Force push (only do this on your feature branch, never on main!)
git push origin feature/never-enough-tests-stress-suite --force-with-lease
```

## Contribution Guidelines

### Code Quality
- Follow pytest's existing code style
- Keep test functions focused and well-named
- Add docstrings to complex test functions
- Ensure C++ code compiles without warnings

### Testing
- All tests must pass before submitting PR
- Add tests for any new features
- Ensure cross-platform compatibility where possible
- Verify C++ components work on target platforms

### Documentation
- Update README.md if adding new features
- Document any new configuration options
- Include examples for complex test patterns
- Keep RESULTS.md updated with latest findings

### Commit Messages
- Use descriptive commit messages
- Follow conventional commit format when possible
- Reference issue numbers if applicable
- Keep commits atomic (one logical change per commit)

## Need Help?

- Check the main pytest CONTRIBUTING.rst for general guidelines
- Join the pytest Discord/Gitter for questions
- Open a discussion issue before major changes
- Review existing PRs for examples

## Current Status

**Branch**: `feature/never-enough-tests-stress-suite`
**Files Added**: 16 files, 3,720+ lines
**Test Count**: 1,660 tests
**Last Validated**: pytest 9.1.0.dev107+g8fb7815f1

## Common Issues

### C++ Compilation Fails
```bash
# Install build essentials
sudo apt-get install build-essential  # Ubuntu/Debian
brew install gcc  # macOS
```

### Tests Fail on Your System
```bash
# Ensure all plugins are installed
pip install -r testing/never_enough_tests/requirements.txt

# Check pytest version
python -m pytest --version

# Rebuild C++ components
cd testing/never_enough_tests/cpp_components && make clean && make
```

### Permission Denied on Scripts
```bash
# Make scripts executable
chmod +x testing/never_enough_tests/scripts/*.sh
chmod +x testing/never_enough_tests/QUICKSTART.sh
```

## License

By contributing to pytest, you agree that your contributions will be licensed under the MIT License.
