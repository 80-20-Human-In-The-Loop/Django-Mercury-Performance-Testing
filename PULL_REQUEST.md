# Remove Abandoned mercury_test Command and Enhance Educational Mode

## Summary

This PR removes the abandoned `mercury_test` Django management command and ensures the educational mode works properly through the documented TEST_RUNNER approach. Django Mercury is a library that users import classes and functions from, not a Django app with management commands.

## Changes Made

### 🗑️ Removed
- **Deleted `django_mercury/cli/management/` directory** (305 lines)
  - Removed abandoned `mercury_test` management command that was never intended to be part of the library
  - This command approach didn't align with Django Mercury being an importable library

### ✨ Enhanced
- **Educational Components** (~2150 lines added/modified)
  - Expanded quiz system with comprehensive questions for different learning levels
  - Enhanced interactive UI with rich terminal support
  - Improved educational guidance with detailed performance explanations
  - Added learning paths for progressive skill development

### 📝 Fixed
- **Documentation**
  - Updated issue template to show correct usage: `python manage.py test --edu` (not `mercury_test --edu`)

## How Educational Mode Works Now

Users configure it in their Django settings as documented:

```python
# settings.py
import sys
if '--edu' in sys.argv:
    TEST_RUNNER = 'django_mercury.test_runner.EducationalTestRunner'
```

Then run tests with:
```bash
python manage.py test --edu
```

## Testing

✅ Verified the EducationalTestRunner works correctly:
- Educational mode activates with `--edu` flag
- Quiz system initializes properly
- Progress tracker functions correctly
- Interactive UI displays when rich library is available

## Related Issue

Partially implements #6 - Interactive Educational Testing Mode

## Breaking Changes

None - the `mercury_test` command was never released or documented as part of the public API.

## Checklist

- [x] Code follows project style guidelines
- [x] Tests pass locally
- [x] Documentation updated where necessary
- [x] CHANGELOG.md will be updated
- [x] No breaking changes to public API