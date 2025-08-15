#!/bin/bash
# Fix Django Test Database Permission Issues

echo "🔧 Django Test Database Permission Fixer"
echo "========================================"
echo ""

# Get the directory where the script was called from
PROJECT_DIR="${1:-$(pwd)}"

echo "📁 Checking project directory: $PROJECT_DIR"

# Check if it's a Django project
if [ ! -f "$PROJECT_DIR/manage.py" ]; then
    echo "❌ Error: manage.py not found in $PROJECT_DIR"
    echo "   Please run this script from your Django project directory or provide the path as an argument."
    exit 1
fi

echo "✅ Found Django project"
echo ""

# Remove old test databases
echo "🗑️  Removing old test databases..."
rm -f "$PROJECT_DIR"/test_*.sqlite3 2>/dev/null
rm -f "$PROJECT_DIR"/test_*.db 2>/dev/null
rm -f "$PROJECT_DIR"/*.sqlite3.test* 2>/dev/null
rm -f "$PROJECT_DIR"/.test_* 2>/dev/null

echo "✅ Old test databases removed"
echo ""

# Fix directory permissions
echo "🔐 Fixing directory permissions..."
chmod 755 "$PROJECT_DIR"

# Fix existing database permissions if they exist
if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
    chmod 664 "$PROJECT_DIR/db.sqlite3"
    echo "✅ Fixed permissions for db.sqlite3"
fi

echo ""
echo "🎯 Database permissions fixed!"
echo ""
echo "💡 For faster tests, add this to your Django settings.py:"
echo ""
echo "import sys"
echo "if 'test' in sys.argv or 'test_coverage' in sys.argv:"
echo "    DATABASES['default'] = {"
echo "        'ENGINE': 'django.db.backends.sqlite3',"
echo "        'NAME': ':memory:',  # In-memory database for speed!"
echo "    }"
echo ""
echo "Or for persistent test database with proper permissions:"
echo ""
echo "DATABASES = {"
echo "    'default': {"
echo "        'ENGINE': 'django.db.backends.sqlite3',"
echo "        'NAME': BASE_DIR / 'db.sqlite3',"
echo "        'TEST': {"
echo "            'NAME': BASE_DIR / 'test_db.sqlite3',"
echo "            'MODE': '0664',  # Ensure writable permissions"
echo "        }"
echo "    }"
echo "}"
echo ""
echo "✅ Now try running: mercury-test --visual users"