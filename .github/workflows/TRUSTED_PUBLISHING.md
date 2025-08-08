# Setting Up Trusted Publishing for Test PyPI

Trusted Publishing (OIDC) eliminates the need for API tokens and provides better security. Here's how to set it up:

## Steps to Configure Trusted Publishing

### 1. Go to Test PyPI
Visit https://test.pypi.org and log in to your account.

### 2. Create/Configure Your Project
- If the project doesn't exist, create it first by manually uploading a package
- Go to your project page: https://test.pypi.org/manage/project/django-mercury-performance/

### 3. Add Trusted Publisher
Navigate to "Publishing" settings and add a new trusted publisher with these details:

- **Owner**: `80-20-Human-In-The-Loop`
- **Repository**: `Django-Mercury-Performance-Testing`
- **Workflow name**: `build_wheels.yml`
- **Environment**: (leave blank for now)

### 4. Update Workflow
Once configured, update the workflow to remove the password field:

```yaml
- name: Publish to Test PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
    # No password needed with trusted publishing!
    packages-dir: upload/
    skip-existing: true
    verbose: true
```

## Alternative: Using API Tokens (Current Setup)

If you prefer to continue using API tokens:

### 1. Generate a New Token
- Go to https://test.pypi.org/manage/account/token/
- Create a new API token with upload permissions
- Copy the token (starts with `pypi-`)

### 2. Update GitHub Secret
- Go to repository Settings → Secrets and variables → Actions
- Update `TEST_PYPI_API_TOKEN` with the new token

### 3. Verify Token Format
The token should:
- Start with `pypi-`
- Be properly scoped for uploads
- Not have expired

## Troubleshooting

### 400 Bad Request Errors
This usually means:
1. Version already exists (even partially)
2. Invalid package metadata
3. Token/authentication issues

### Solutions:
1. Increment version in `pyproject.toml`
2. Check package metadata is valid
3. Use verbose mode to see detailed errors
4. Try manual upload with `twine` to isolate issues

## Manual Testing

To test uploads manually:
```bash
pip install twine
python -m build
twine upload --repository testpypi dist/* --verbose
```

This will prompt for username (use `__token__`) and password (use your API token).