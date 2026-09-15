#!/bin/bash
# Unified Backend Complete - Deployment Package Builder
# Builds optimized Lambda deployment package for production

set -e

echo "🔨 Building Unified Backend Lambda Deployment Package..."
echo "=================================================="

# Clean previous builds
echo "📦 Cleaning previous builds..."
rm -rf build/ lambda_deployment.zip 2>/dev/null || true

# Create build directory
mkdir -p build

# Install dependencies for arm64 (Lambda runs on ARM)
echo "📥 Installing dependencies for Lambda (arm64)..."
# Use minimal requirements for Lambda size constraints (50MB limit)
# Use requirements-lambda.txt if it exists, otherwise fall back to requirements.txt
REQS_FILE="requirements-lambda.txt"
if [ ! -f "$REQS_FILE" ]; then
    REQS_FILE="requirements.txt"
fi
echo "Using requirements file: $REQS_FILE"
# Try using Python 3.12 directly if available
PYTHON_CMD="python3.12"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Install dependencies using correct platform flags for Lambda compatibility
echo "Installing for manylinux2014_aarch64 platform (AWS Lambda)..."
$PYTHON_CMD -m pip install \
  --platform manylinux2014_aarch64 \
  --target=build \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --no-cache-dir \
  -r "$REQS_FILE"

# Copy application code
echo "📄 Copying application code..."
cp lambda_handler.py build/
cp -r app build/

# Remove unnecessary files to reduce size
echo "🗑️  Optimizing package size..."
cd build
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true

# Create deployment package
echo "📦 Creating lambda_deployment.zip..."
cd ..
zip -r -q lambda_deployment.zip build/

# Report results
PACKAGE_SIZE=$(du -sh lambda_deployment.zip | cut -f1)
echo ""
echo "✅ Lambda Deployment Package Ready!"
echo "=================================================="
echo "📦 File: lambda_deployment.zip"
echo "📊 Size: $PACKAGE_SIZE"
echo ""
echo "Next steps:"
echo "  1. cd terraform/"
echo "  2. terraform init"
echo "  3. terraform plan"
echo "  4. terraform apply"
echo ""
