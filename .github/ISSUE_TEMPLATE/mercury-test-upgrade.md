---
name: Mercury-Test CLI Major Upgrade
about: Comprehensive upgrade to mercury-test with smart discovery and QOL features
title: "[UPGRADE] Mercury-Test CLI 2.0 - Smart Discovery & Comprehensive QOL Features"
labels: 'enhancement, cli, student-friendly, professional-tools, major-upgrade'
assignees: ''

---

## Claiming This Task:

Before you start working, please check the **Assignees** section on the right. If no one is assigned, leave a comment claiming the issue and assign it to yourself. This is required to prevent duplicate work.

## **Vision: Next-Generation Django Testing CLI** 🚀

Transform `mercury-test` from a simple educational wrapper into a comprehensive, intelligent Django testing companion that adapts to users from complete beginners to seasoned professionals.

## **Current Situation**

The current `mercury-test` tool is functional but has several limitations:

- **Limited Discovery**: Only checks current directory and up to 3 parent directories for `manage.py`
- **Basic Interface**: Simple command-line interface without modern UX features
- **No User Adaptation**: Same experience for beginners and experts
- **Limited Feedback**: Basic performance hints, no comprehensive guidance
- **No Intelligence**: Doesn't learn from user patterns or project structure

**Pain Points:**
- Students get lost when `manage.py` isn't found
- Professionals lack advanced features they expect from modern tools
- No guidance for common Django testing mistakes
- No integration with modern development workflows

## **Proposed Solution: Mercury-Test CLI 2.0**

### 🎯 **Core Feature 1: Intelligent manage.py Discovery**

**Smart Three-Tier Search Strategy:**
```python
def find_manage_py_intelligent():
    # Tier 1: Fast search (current + parents)
    manage_py = search_current_and_parents()
    if manage_py: return manage_py
    
    # Tier 2: Common patterns (sibling app directories)
    manage_py = search_sibling_app_dirs() 
    if manage_py: return manage_py
    
    # Tier 3: Deep search with progress (children + subdirs)
    manage_py = search_children_with_progress()
    return manage_py
```

**Features:**
- 🔍 **Current Directory**: Instant check
- ⬆️ **Parent Directories**: Up to project root or 5 levels
- 👥 **Sibling App Check**: Look in `../` for common Django app structure
- ⬇️ **Recursive Child Search**: With progress bar for large directories
- 💾 **Location Caching**: Remember found locations for faster subsequent runs
- 🎯 **Smart Heuristics**: Prefer `manage.py` files near Django apps

**Example Output:**
```
🔍 Searching for Django project...
├─ Current directory... ❌
├─ Parent directories... ❌  
├─ Sibling app directories... ❌
├─ Searching subdirectories... ⏳ [████████░░] 80% (42/52 dirs)
└─ Found manage.py at: ./my_project/manage.py ✅
```

---

### 👨‍🎓 **Student/Beginner Features**

#### **1. Test Wizard Mode** (`--wizard`)
Interactive test selection and configuration:
```bash
mercury-test --wizard
```
```
🧙 Django Mercury Test Wizard
╔══════════════════════════════════════╗
║ What would you like to test today?   ║
╠══════════════════════════════════════╣
║ [1] Run all tests                    ║
║ [2] Test specific app                ║
║ [3] Test single test file            ║
║ [4] Test specific function           ║
║ [5] Generate new test                ║
╚══════════════════════════════════════╝
```

#### **2. Explain Mode** (`--explain`)
Educational explanations before running tests:
```bash
mercury-test users.tests --explain
```
```
📚 About to run: users.tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This will test all functionality in your 'users' app.
Test files found:
├─ test_models.py (tests your User model)
├─ test_views.py (tests your API endpoints)  
└─ test_forms.py (tests form validation)

💡 TIP: This might take 2-3 minutes. Want to test just one file instead?
Try: mercury-test users.tests.test_models

Continue? [Y/n] 
```

#### **3. Auto-Fix Suggestions** (`--suggest-fixes`)
Detect and suggest fixes for common issues:
```python
# Detects common test mistakes:
- Missing database transactions
- Hardcoded paths
- Time-dependent tests
- Missing test data cleanup
- Incorrect assertion usage
```

#### **4. Test Generation** (`--generate`)
Create test boilerplate:
```bash
mercury-test --generate users.models.User
```
```python
# Generated: users/tests/test_user_model.py
class TestUserModel(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
    
    def test_user_creation(self):
        """Test user can be created successfully."""
        self.assertTrue(isinstance(self.user, User))
        self.assertEqual(self.user.username, 'testuser')
    
    # TODO: Add more specific tests for your User model
```

#### **5. Visual Progress & Feedback**
Rich visual output with educational context:
```
🎓 Educational Mode | Level: Beginner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Running tests: users.tests.test_models
░░░░░░░░░░░░░░░░░░░░ 0% | Preparing test database...
██████████░░░░░░░░░░ 50% | Running 5/10 tests... 
████████████████████ 100% | All tests completed! ✅

📊 Results:
├─ test_user_creation ✅ (45ms) 
├─ test_user_validation ✅ (23ms)
└─ test_user_deletion ❌ (failed - see explanation below)

🎯 Learning Moment: Why did test_user_deletion fail?
Your test tried to delete a user but didn't check if the deletion
actually worked. Here's how to fix it...
```

---

### 👨‍💻 **Professional/Expert Features**

#### **1. Watch Mode** (`--watch`)
Auto-rerun tests on file changes:
```bash
mercury-test --watch --filter="users"
```
```
👀 Watching for changes in:
├─ users/ (models, views, tests)
├─ templates/users/
└─ static/users/

Press 'a' to run all tests, 'q' to quit
File changed: users/models.py → Running related tests...
```

#### **2. Advanced Profiling** (`--profile`)
Detailed performance analysis:
```bash
mercury-test --profile --output=json
```
```json
{
  "total_time": 45.6,
  "test_breakdown": {
    "users.tests.test_models": {
      "time": 12.3,
      "queries": 15,
      "memory_peak": "45MB",
      "slowest_test": "test_bulk_operations"
    }
  },
  "bottlenecks": [
    {
      "type": "n_plus_one",
      "location": "users/tests/test_views.py:42",
      "suggestion": "Use select_related('profile')"
    }
  ]
}
```

#### **3. Parallel Optimization** (`--parallel=auto`)
Intelligent parallel execution:
```python
# Auto-detects:
- CPU core count
- Test dependencies
- Database constraints  
- Optimal chunk sizes
```

#### **4. Test Prioritization** (`--priority=smart`)
Run important tests first:
```python
# Priority order:
1. Recently failed tests
2. Tests for recently changed files
3. Critical path tests (tagged)
4. Fastest tests first
5. Remaining tests
```

#### **5. CI/CD Integration**
Multiple output formats:
```bash
mercury-test --output=junit    # JUnit XML
mercury-test --output=github   # GitHub Actions format
mercury-test --output=sonar    # SonarQube format
```

---

### 🌟 **Universal QOL Features**

#### **1. Smart Test Selection**
Fuzzy matching and intelligent suggestions:
```bash
mercury-test usr.mdl        # → users.models
mercury-test login          # → finds all login-related tests
mercury-test "slow tests"   # → runs tests tagged as slow
```

#### **2. Configuration Profiles**
Save and reuse common configurations:
```bash
# Save current config
mercury-test --save-profile=quick-check

# Use saved profile  
mercury-test --profile=quick-check

# List profiles
mercury-test --list-profiles
```

```toml
# ~/.mercury/profiles/quick-check.toml
[profile]
name = "Quick Check"
parallel = 4
verbosity = 1
tags = ["fast", "critical"]
exclude = ["slow", "integration"]
```

#### **3. Multi-Project Support**
Handle multiple Django projects:
```bash
mercury-test --project=api users.tests     # Test API project
mercury-test --project=frontend auth/      # Test frontend project
mercury-test --list-projects               # Show all projects
```

#### **4. Database Snapshots** (`--snapshot`)
Quick database reset between runs:
```bash
mercury-test --snapshot=create baseline    # Create snapshot
mercury-test --snapshot=restore baseline   # Restore to snapshot
```

#### **5. Smart Notifications**
Desktop and system notifications:
```python
# When tests complete:
🔔 Django Tests Complete
   ✅ 45 passed, ❌ 2 failed
   Duration: 2m 34s
   [Click to see results]
```

#### **6. Test Report Generation**
Rich HTML reports with analytics:
```bash
mercury-test --report=html --output=reports/
```
```html
<!DOCTYPE html>
<html>
<head><title>Test Report - MyProject</title></head>
<body>
  <!-- Interactive charts, timelines, coverage maps -->
  <div class="summary">
    <h2>Test Run Summary</h2>
    <canvas id="performanceChart"></canvas>
  </div>
</body>
</html>
```

---

## **Implementation Plan**

### **Phase 1: Core Intelligence** (Weeks 1-2)
- [ ] Implement smart manage.py discovery
- [ ] Add location caching system
- [ ] Create progress indicators for slow searches

### **Phase 2: Student Features** (Weeks 3-4)  
- [ ] Build interactive wizard mode
- [ ] Add explain mode with educational content
- [ ] Implement test generation templates
- [ ] Create visual progress system

### **Phase 3: Professional Tools** (Weeks 5-6)
- [ ] Add watch mode with file monitoring
- [ ] Implement advanced profiling
- [ ] Build parallel optimization
- [ ] Add CI/CD output formats

### **Phase 4: Universal QOL** (Weeks 7-8)
- [ ] Smart test selection with fuzzy matching
- [ ] Configuration profiles system
- [ ] Multi-project support
- [ ] Rich reporting system

### **Phase 5: Polish & Integration** (Weeks 9-10)
- [ ] Notification system
- [ ] Database snapshot functionality
- [ ] Comprehensive testing
- [ ] Documentation updates

---

## **Files to be Altered or Created**

### **Core Files:**
- `django_mercury/cli/mercury_test.py` - Main CLI logic upgrade
- `django_mercury/cli/discovery.py` - Smart manage.py discovery
- `django_mercury/cli/cache.py` - Location caching system

### **Student Features:**
- `django_mercury/cli/wizard.py` - Interactive wizard mode
- `django_mercury/cli/explain.py` - Educational explanations
- `django_mercury/cli/generator.py` - Test template generation
- `django_mercury/cli/visual.py` - Rich visual progress

### **Professional Features:**
- `django_mercury/cli/watch.py` - File watching and auto-rerun
- `django_mercury/cli/profiler.py` - Advanced performance profiling  
- `django_mercury/cli/parallel.py` - Intelligent parallel execution
- `django_mercury/cli/cicd.py` - CI/CD integrations

### **Universal Features:**
- `django_mercury/cli/selector.py` - Smart test selection
- `django_mercury/cli/profiles.py` - Configuration management
- `django_mercury/cli/multiproject.py` - Multi-project support
- `django_mercury/cli/reports.py` - Report generation
- `django_mercury/cli/notifications.py` - System notifications

### **Configuration:**
- `~/.mercury/config.toml` - Global configuration
- `~/.mercury/profiles/` - Saved test profiles
- `~/.mercury/cache/` - Project location cache

---

## **Success Metrics**

### **Quantitative:**
- [ ] ⚡ 90% reduction in "manage.py not found" errors
- [ ] 📈 50% increase in student test writing (measured by test generation usage)
- [ ] 🏃‍♂️ 30% faster test execution for professionals (via smart features)
- [ ] 🎯 95% user satisfaction in discovery system

### **Qualitative:**
- [ ] 🎓 Students find testing approachable and educational
- [ ] 💼 Professionals adopt mercury-test as daily driver
- [ ] 🌟 Community contributions increase due to improved DX
- [ ] 📚 Tool becomes go-to Django testing tutorial reference

---

## **Benefits**

### **For Students:**
- **Removes barriers**: Smart discovery eliminates "manage.py not found" frustration
- **Educational**: Learn Django testing best practices through guided experience
- **Confidence building**: Visual feedback and explanations reduce intimidation
- **Practical skills**: Generate real, working test code

### **For Professionals:**
- **Productivity**: Watch mode, smart selection, and parallel optimization save time
- **Integration**: Works seamlessly with existing CI/CD pipelines
- **Intelligence**: Learns from patterns to suggest optimizations
- **Comprehensive**: One tool for all Django testing needs

### **For Django Community:**
- **Accessibility**: Lower barrier to entry for Django testing
- **Standards**: Promotes testing best practices through education
- **Innovation**: Showcases what modern Django tooling can be
- **Growth**: More developers writing better tests

---

## **Example User Journeys**

### **Complete Beginner:**
```
1. Downloads Django tutorial project
2. cd tutorial/polls/  (in wrong directory)
3. mercury-test --wizard
4. Tool finds manage.py in parent directory
5. Wizard guides through first test run
6. Explains what each test does
7. Celebrates successful test run with visual feedback
```

### **Professional Developer:**
```
1. Working on complex Django project
2. mercury-test --watch --profile=backend-api 
3. Makes code changes, tests auto-run
4. Gets instant feedback on performance regressions
5. Uses profiling data to optimize slow tests
6. Saves optimized configuration as new profile
```

### **CI/CD Pipeline:**
```
1. Git push triggers CI
2. mercury-test --parallel=auto --output=github --profile=ci
3. Intelligent parallel execution speeds up pipeline
4. Rich GitHub Actions integration shows detailed results
5. Performance metrics tracked over time
```

---

## **Additional Context**

This upgrade transforms mercury-test from a simple educational wrapper into a comprehensive Django testing platform that grows with users from their first test to production deployments.

**Inspiration from modern tools:**
- **Jest** (watch mode, smart testing)
- **Pytest** (fixture system, detailed output)
- **GitHub CLI** (intuitive UX, rich formatting)
- **VS Code** (intelligent discovery, user adaptation)

**Technical considerations:**
- Backward compatibility with existing mercury-test usage
- Performance optimization for large codebases
- Cross-platform support (Windows, macOS, Linux)
- Integration with existing Django ecosystem tools

**Future possibilities:**
- Integration with Django Debug Toolbar
- AI-powered test suggestions
- Integration with Django Channels for async testing
- Plugin system for custom test runners