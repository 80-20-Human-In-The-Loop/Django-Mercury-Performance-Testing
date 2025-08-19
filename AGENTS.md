# Agent Guidelines for Django Mercury Performance Testing

*Building tools that make humans smarter, not obsolete. Automate the mundane, preserve the meaningful.*

## Build/Test Commands
- **Run all tests**: `python test_runner.py` (main test runner) or `pytest tests/`
- **Run single test**: `pytest tests/path/to/test_file.py::TestClass::test_method`
- **Run with coverage**: `pytest --cov=django_mercury tests/`
- **Lint/Format**: `ruff check django_mercury/`, `black django_mercury/`, `isort django_mercury/`
- **Type check**: `mypy django_mercury/ --ignore-missing-imports`
- **Build package**: `python -m build`

## Code Style Guidelines
- **Line length**: 100 characters (Black/Ruff configured)
- **Import order**: FUTURE, STDLIB, DJANGO, THIRDPARTY, FIRSTPARTY, LOCALFOLDER (isort profile: black)
- **Type hints**: Required for new code, gradual adoption for existing code (see pyproject.toml mypy config)
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Docstrings**: Google style for all public functions/classes
- **Error handling**: Use specific exception types, avoid bare except clauses
- **Django sections**: Known django imports: ["django", "rest_framework"]

## 80-20 Human-in-the-Loop Philosophy

### Three Audience Pattern
Design for **Beginners** (--edu flag), **Experts** (default), and **AI Agents** (--agent flag):

**Educational Mode** (`--edu`):
- Provide detailed explanations and learning context
- Show "What/Why/How" for each issue found
- Include links to documentation and learning resources
- Use progressive disclosure to avoid information overload

**Professional Mode** (default):
- Concise, actionable output focused on efficiency
- Quick fixes for trivial issues, detailed analysis for complex ones
- Respect expert time with fast execution and clear results

**Agent Mode** (`--agent`, MCP servers):
- Structured JSON output for programmatic consumption
- Preserve human decision points for architectural changes
- Clear flags for `requires_human_review` on critical issues

### Human Decision Preservation
- **Never auto-fix architectural changes** without human review
- **Always explain** the reasoning behind suggestions
- **Preserve learning opportunities** - don't just fix, teach why
- **Flag complex issues** that require human understanding of context

## Testing Standards
- Use `DjangoMercuryAPITestCase` for performance-aware tests
- Mark tests: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Test files: `test_*.py` pattern in `tests/` directory
- Use `self.configure_mercury()` in test setup for performance monitoring
- **Educational tests**: Include explanations in test failures to teach debugging

## Error Messages That Teach
Transform errors into learning opportunities:
- Start with the immediate problem
- Explain why it matters (performance/security impact)
- Provide specific fix suggestions
- Link to relevant documentation or examples
- For beginners: Include conceptual explanations

## Progressive Disclosure
- **Level 1**: Summary of issues found
- **Level 2** (`--verbose`): Detailed technical information
- **Level 3** (`--edu`): Full educational context with examples
- Allow users to drill down based on their needs and expertise

## Educational Features Enhancement
- **Student mode with hints/learn plugins**: Always show learning content, even for passing tests
- **Learning suggestions**: Display `--learn` command suggestions based on test context
- **Profile switching hints**: Guide users to expert mode when appropriate
- **Contextual tips**: Show educational content during test execution, not just when issues occur
