# Django Mercury Performance Testing - Ready for PyPI 🚀

## ✅ Package Setup Complete

Your Django Mercury Performance Testing framework is now ready for deployment to PyPI as version 0.0.1!

## 📦 Package Details
- **Package Name**: `django-mercury-performance`
- **Version**: 0.0.1
- **License**: GPL-3.0
- **Python Support**: 3.8+
- **Django Support**: 3.2 - 5.1

## 🏗️ Project Structure
```
.
├── django_mercury/          # Main package
│   ├── __init__.py         # Package initialization (v0.0.1)
│   ├── c_core/             # C extensions for performance
│   ├── python_bindings/    # Python interfaces
│   ├── documentation/      # API documentation
│   └── examples/           # Usage examples
├── tests/                   # Unit tests (moved from src/)
├── pyproject.toml          # Modern Python packaging config
├── MANIFEST.in             # Package file inclusion rules
├── deploy.sh               # Deployment script
├── README.md               # Main documentation
├── CHANGELOG.md            # Release history
└── LICENSE                 # GPL-3.0 license
```

## 🚀 To Deploy to PyPI

### 1. Get PyPI Token
1. Go to https://pypi.org/manage/account/token/
2. Create an API token for uploading packages
3. Copy the token (starts with `pypi-`)

### 2. Configure Token
Edit `.env` file and add your token:
```bash
PYPI_TOKEN=pypi-your-actual-token-here
```

### 3. Build C Extensions (if needed)
```bash
cd django_mercury/c_core
make clean && make
cd ../..
```

### 4. Deploy!
```bash
# Test run first (no actual upload)
./deploy.sh --dry-run

# Deploy to PyPI
./deploy.sh
```

## 📋 What Changed from Original

1. **Renamed Package**: From `src/` to `django_mercury/`
2. **Modern Packaging**: Replaced `setup.py` with `pyproject.toml`
3. **Moved Tests**: Tests now in root `tests/` directory
4. **Moved Runners**: Test runners moved to project root
5. **Updated Metadata**: Changed from EduLite to Django Mercury branding
6. **Version**: Set to 0.0.1 for initial release
7. **Deployment Script**: Created custom `deploy.sh` adapted from Storm Logger

## 🎯 Post-Deployment

After successful deployment, users can install with:
```bash
pip install django-mercury-performance
```

Then use in their Django tests:
```python
from django_mercury import DjangoMercuryAPITestCase

class MyPerformanceTest(DjangoMercuryAPITestCase):
    def test_api_performance(self):
        response = self.client.get('/api/endpoint/')
        # Performance automatically monitored!
```

## ⚠️ Important Notes

1. **C Extensions**: The C core libraries need to be compiled before packaging
2. **Django Required**: The package requires Django to be installed for full functionality
3. **First Release**: This is v0.0.1 - the package name is not yet taken on PyPI

## 🔧 Troubleshooting

If deployment fails:
1. Check your PyPI token in `.env`
2. Ensure you're in a virtual environment
3. Try `--dry-run` first to test the process
4. Check that the package name isn't taken: `pip search django-mercury`

## 📞 Support

For issues or questions about the deployment process, refer to:
- The deployment script help: `./deploy.sh --help`
- PyPI documentation: https://packaging.python.org/
- Django packaging guide: https://docs.djangoproject.com/en/stable/intro/reusable-apps/

---

**Ready to ship! 🚢** Just add your PyPI token and run `./deploy.sh`