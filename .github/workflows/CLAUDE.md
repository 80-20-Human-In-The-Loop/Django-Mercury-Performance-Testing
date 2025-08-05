# 🚀 GitHub Actions Deployment Guide

> **Making deployment accessible to everyone through the 80-20 Human in the Loop philosophy**

## 📋 Table of Contents

- [What is GitHub Actions?](#what-is-github-actions)
- [The 80-20 Philosophy in Deployment](#the-80-20-philosophy-in-deployment)
- [How Our Workflows Work](#how-our-workflows-work)
- [For Beginners](#for-beginners-your-first-deployment)
- [For Experts](#for-experts-advanced-configuration)
- [For AI Agents](#for-ai-agents-automation-integration)
- [Troubleshooting](#troubleshooting-common-issues)
- [Contributing](#contributing-to-deployment)

---

## What is GitHub Actions?

GitHub Actions is like a robot assistant that helps with your code. When you push code to GitHub, this robot can:

- ✅ Test your code automatically
- 📦 Build packages for others to use
- 🌍 Publish your work to PyPI (Python Package Index)
- 🔄 Do all of this on Windows, Mac, and Linux

**In simple terms**: GitHub Actions saves you time by doing repetitive tasks automatically.

### Why This Matters

Without automation:
- You test on your computer only (might miss bugs on other systems)
- You build packages manually (takes time, prone to errors)
- You upload to PyPI manually (easy to forget steps)

With GitHub Actions:
- Tests run on 9 different setups automatically
- Packages build for all platforms while you sleep
- Publishing happens with one click or tag

---

## The 80-20 Philosophy in Deployment

Our deployment follows the **80-20 Human in the Loop** principle:

### 80% Automated (What the Robot Does)

```yaml
# The robot handles:
- Running 800+ tests on 3 operating systems
- Building packages for 5+ Python versions
- Checking code quality
- Creating distribution files
- Uploading to PyPI
```

### 20% Human Control (What You Decide)

```yaml
# Humans decide:
- When to release (create a version tag)
- What version number to use
- Whether tests must pass before release
- Which platforms to support
- Security and API tokens
```

### Why This Balance Works

**Full automation (100%) is dangerous**:
- Broken code could deploy automatically
- Security issues might slip through
- No human review of what ships to users

**Our approach (80-20) is safer**:
- Humans control WHEN deployment happens
- Robots handle HOW deployment works
- Humans can stop bad releases
- Robots can't make security decisions

---

## How Our Workflows Work

We have two main workflows:

### 1. Test Build (`test_build.yml`)

**What it does**: Quick check that the package can build

**When it runs**: Every push to main branch

**Simple diagram**:
```
Code Push → Build Test → Import Test → ✅ or ❌
```

### 2. Build and Deploy (`build_wheels.yml`)

**What it does**: Complete testing, building, and deployment

**When it runs**: 
- Every push to main
- When you create a version tag (v1.0.0)
- Manual trigger for test releases

**⚠️ CRITICAL: C Extensions are REQUIRED in CI**

The CI will **FAIL** if C extensions cannot be built. This is intentional because:
- Pure Python fallback is 10-100x slower
- Performance tests will fail with pure Python
- C extensions are the primary performance feature

**Complete flow**:
```
         ┌─────────────┐
         │ Code Push   │
         └──────┬──────┘
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
┌─────────┐          ┌─────────────┐
│ Tests   │          │ Build Wheels│
│ (3 OS)  │          │ (All OS)    │
└────┬────┘          └──────┬──────┘
     │                      │
     │ (Tests can fail)     │
     │                      │
     └──────────┬───────────┘
                │
                ▼
         ┌─────────────┐
         │Check Builds │
         └──────┬──────┘
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
┌──────────┐         ┌─────────────┐
│Test PyPI │         │ Real PyPI   │
│(Manual)  │         │ (Tags only) │
└──────────┘         └─────────────┘
```

### Key Design Decisions

1. **Tests Don't Block Deployment**
   - Why: Sometimes we need to ship fixes even if some tests fail
   - Human decides if failures are acceptable

2. **C Extensions Are MANDATORY in CI**
   - **Changed Policy**: C extensions MUST build in CI (no fallback)
   - Why: Pure Python is 10-100x slower and fails performance tests
   - User systems can still fall back to pure Python if needed
   - CI ensures we always ship working C extensions

3. **Multiple Python Versions**
   - Why: Users have different Python installations
   - We support Python 3.8 to 3.12

---

## For Beginners: Your First Deployment

### Understanding the Basics

Think of deployment like mailing a package:
1. Test it works (run tests)
2. Pack it nicely (build wheels)
3. Send it out (publish to PyPI)

### Step 1: Watch Automatic Tests

When you push code:

```bash
git add .
git commit -m "Fix bug in performance monitor"
git push
```

GitHub Actions starts automatically! Watch it work:

1. Go to your repository on GitHub
2. Click "Actions" tab
3. See your workflow running

**What you'll see**:
- 🟡 Yellow dot = running
- ✅ Green check = passed
- ❌ Red X = failed

### Step 2: Create a Test Release

Want to test the full process?

1. Go to "Actions" tab
2. Click "Build and Test Wheels"
3. Click "Run workflow"
4. Check "Publish to Test PyPI"
5. Click green "Run workflow" button

### Step 3: Make a Real Release

Ready to share with the world?

```bash
# 1. Update version in setup.py
# Change version = "0.5.10" to version = "0.5.11"

# 2. Commit the change
git add setup.py
git commit -m "Bump version to 0.5.11"

# 3. Create a version tag
git tag v0.5.11

# 4. Push everything
git push origin main
git push origin v0.5.11
```

The workflow runs automatically and publishes to PyPI!

### Understanding Failures

Tests failed? Don't panic!

**Common reasons**:
- Tests work on your computer but fail on others
- Windows has different behavior than Mac/Linux
- Network issues during testing

**What to do**:
1. Click on the failed job
2. Read the error message
3. Fix the issue or ask for help
4. Push again

---

## For Experts: Advanced Configuration

### Workflow Architecture

Our dual-workflow system provides flexibility:

```yaml
test_build.yml:
  purpose: Rapid feedback on build viability
  runtime: ~2 minutes
  triggers: [push:main, workflow_dispatch]
  
build_wheels.yml:
  purpose: Full CI/CD pipeline
  runtime: ~15-30 minutes
  triggers: [push:main, push:tags:v*, PR, workflow_dispatch]
```

### Key Configuration Points

#### 1. Test Matrix Strategy

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ['3.8', '3.10', '3.12']
```

**Customization options**:
- Add `python-version: ['3.9', '3.11']` for complete coverage
- Remove `windows-latest` if Windows support isn't needed
- Add `ubuntu-20.04` for older Linux compatibility

#### 2. C Extension Handling

```yaml
- name: Build C libraries (Linux/macOS)
  if: runner.os != 'Windows'
  run: |
    if ! make ci; then
      echo "❌ ERROR: C library build failed!"
      echo "C extensions are REQUIRED in CI - pure Python is too slow!"
      exit 1  # FAIL the build - no fallback allowed
    fi
```

**Updated Design Philosophy (as of August 2025)**:
- **CI**: C extensions MUST build - no fallback to pure Python
- **User systems**: Graceful fallback still allowed
- **Rationale**: Pure Python is 10-100x slower, breaks performance tests
- **Result**: We guarantee C extensions work for all releases

#### 3. Publishing Configuration

```yaml
publish:
  needs: [check_build]  # Note: NOT dependent on test_wheels
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
```

**Security considerations**:
- Requires `PYPI_API_TOKEN` secret
- Only triggers on protected tags
- Manual approval possible via `workflow_dispatch`

### Advanced Patterns

#### Custom Wheel Building

```yaml
env:
  CIBW_BUILD: "cp38-* cp39-* cp310-* cp311-* cp312-*"
  CIBW_SKIP: "*-musllinux_* *-win32"
  CIBW_ARCHS_LINUX: "x86_64"
  CIBW_ARCHS_MACOS: "x86_64 arm64 universal2"
```

#### Platform-Specific Tests

```yaml
- name: Windows-specific tests
  if: runner.os == 'Windows'
  run: |
    # Handle Windows path separators
    python -m pytest tests/windows_specific/
```

---

## For AI Agents: Automation Integration

### Integration Points

AI agents can interact with our deployment system at several points:

#### 1. Monitoring Build Status

```python
# Check workflow status via GitHub API
GET /repos/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/actions/runs

# Response includes:
{
  "workflow_runs": [{
    "status": "completed",
    "conclusion": "success",
    "name": "Build and Test Wheels"
  }]
}
```

#### 2. Triggering Test Builds

```bash
# AI agents can trigger workflow_dispatch events
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/actions/workflows/build_wheels.yml/dispatches \
  -d '{"ref":"main","inputs":{"publish_to_test_pypi":"false"}}'
```

#### 3. Analyzing Test Results

```yaml
# Parse test output for performance metrics
- name: Extract test metrics
  run: |
    python test_runner.py --coverage --ci > test_results.txt
    # AI can parse test_results.txt for:
    # - Test counts
    # - Performance timing
    # - Coverage percentages
```

### Best Practices for AI Integration

1. **Read-Only by Default**
   - AI should monitor and analyze
   - Human approves deployment actions

2. **Semantic Version Analysis**
   ```python
   # AI can suggest version bumps
   if "fix" in commit_message:
       suggest_version = "0.5.11"  # Patch bump
   elif "feat" in commit_message:
       suggest_version = "0.6.0"   # Minor bump
   ```

3. **Failure Pattern Recognition**
   - AI can identify common failure patterns
   - Suggest fixes based on historical data
   - Never auto-fix security-related failures

### MCP Server Integration

For AI agents using the Mercury MCP server:

```python
# Monitor deployment status
@mcp_tool
def check_deployment_status(version: str) -> dict:
    """Check if a version successfully deployed"""
    return {
        "version": version,
        "pypi_published": check_pypi(version),
        "tests_passed": check_github_status(version),
        "platforms_supported": ["windows", "macos", "linux"]
    }
```

---

## Troubleshooting Common Issues

### Issue 1: "Windows CI Can't Check Out Code"

**Error**: `error: invalid path 'django_mercury/c_core/...'`

**Cause**: Windows Git security blocking certain paths

**Solution**:
```yaml
- name: Configure Git for Windows paths
  if: runner.os == 'Windows'
  run: |
    git config --global core.protectNTFS false
    git config --global core.longpaths true
```

### Issue 2: "Unicode Characters Break Windows Tests"

**Error**: `UnicodeEncodeError: 'charmap' codec can't encode character`

**Cause**: Windows uses CP1252 encoding by default

**Solution**:
```yaml
- name: Set UTF-8 encoding
  run: |
    echo "PYTHONIOENCODING=utf-8" >> $GITHUB_ENV
    chcp 65001  # Set console to UTF-8
```

### Issue 3: "C Extensions Fail to Build"

**Error**: `error: Microsoft Visual C++ 14.0 or greater is required`

**Cause**: Missing build tools on Windows

**Solution**: Our workflow automatically falls back to pure Python:
```yaml
echo "DJANGO_MERCURY_PURE_PYTHON=1" >> $GITHUB_ENV
```

### Issue 4: "Tests Pass Locally but Fail in CI"

**Common causes**:
1. **Timezone differences**: CI runs in UTC
2. **File paths**: Windows vs Unix separators
3. **Dependencies**: Different versions in CI

**Debug approach**:
```yaml
- name: Debug environment
  run: |
    python --version
    pip list
    echo "Current directory: $(pwd)"
    echo "Environment variables:"
    env | sort
```

### Issue 5: "C Extensions Build Failed in CI" (CRITICAL)

**Error**: `❌ ERROR: C library build failed!`

**Cause**: Missing build dependencies or compilation errors

**Solution**: The CI now REQUIRES C extensions to build successfully. Common fixes:

1. **Ubuntu**: Ensure build dependencies are installed
   ```yaml
   - name: Install C build dependencies (Ubuntu)
     run: |
       sudo apt-get update
       sudo apt-get install -y build-essential python3-dev
   ```

2. **Check Makefile output**: Look for specific compilation errors
   ```
   gcc: error: unrecognized command line option '-mavx'
   ```

3. **Python headers missing**: Install python-dev package

**IMPORTANT**: We do NOT fall back to pure Python in CI anymore. Fix the build error!

---

## Contributing to Deployment

### For Beginners

Want to help improve deployment? Start here:

1. **Report issues clearly**
   ```markdown
   What happened: Build failed on Windows
   Expected: Build should pass
   Error message: [paste error here]
   Link to failed run: [GitHub Actions URL]
   ```

2. **Test changes locally**
   ```bash
   # Simulate CI environment
   python -m venv test_env
   source test_env/bin/activate  # or test_env\Scripts\activate on Windows
   pip install -e ".[dev]"
   python test_runner.py
   ```

### For Experts

Advanced contributions:

1. **Optimize build times**
   - Cache dependencies
   - Parallelize test runs
   - Skip redundant builds

2. **Add new platforms**
   - ARM64 Linux support
   - FreeBSD runners
   - Older Python versions

3. **Improve security**
   - Signed commits requirement
   - SLSA provenance
   - Dependency scanning

### Following the 80-20 Philosophy

Remember when contributing:

- **80% automation**: Make repetitive tasks automatic
- **20% human control**: Keep important decisions manual
- **100% clarity**: Document why, not just how

**Good PR example**:
```yaml
# Added wheel upload retry because PyPI sometimes has temporary failures
# Human still controls when upload happens, but robot retries if needed
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    retry: 3
    retry-delay: 10
```

---

## Summary

Our GitHub Actions deployment embodies the 80-20 philosophy:

- **Robots** handle testing, building, and uploading
- **Humans** decide when and what to release
- **Everyone** benefits from faster, safer deployments

Whether you're a beginner pushing your first commit or an expert optimizing build times, the system works for you.

**Remember**: The goal isn't to remove humans from deployment. It's to free humans from repetitive work so they can focus on important decisions.

---

*Built with the 80-20 Human in the Loop philosophy - where automation serves humanity, not the other way around.*

## Next Steps

- 🚀 **Try it**: Make a small change and watch the workflows run
- 📚 **Learn more**: Read the [workflow files](.github/workflows/)
- 🤝 **Get help**: Open an issue if something isn't clear
- 💡 **Contribute**: Share your ideas for improvement

**Together, we make deployment accessible to everyone!**