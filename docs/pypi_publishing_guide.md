# 📦 Publishing to PyPI - Complete Guide

This guide walks you through publishing the Workflow Automation Platform to PyPI using GitHub Actions.

## 📋 Prerequisites

### 1. PyPI Account Setup

1. **Create PyPI Account**: https://pypi.org/account/register/
2. **Create Test PyPI Account**: https://test.pypi.org/account/register/
3. **Enable 2FA** on both accounts (required for trusted publishing)

### 2. Configure Trusted Publishing (Recommended)

Trusted publishing eliminates the need for API tokens by using GitHub's OIDC.

#### On PyPI (https://pypi.org):

1. Go to your PyPI account settings
2. Navigate to "Publishing" → "Add a new publisher"
3. Fill in:
   - **PyPI Project Name**: `workflow-automation-platform`
   - **Owner**: `bibektimilsina` (your GitHub username)
   - **Repository name**: `automation`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: Leave blank or use `pypi`

#### On Test PyPI (https://test.pypi.org):

Repeat the same process for Test PyPI to test releases before production.

## 🏗 Project Structure

```
fuse/
├── .github/
│   └── workflows/
│       └── publish-to-pypi.yml    # GitHub Actions workflow
├── fuse_backend/
│   ├── pyproject.toml             # Package metadata
│   ├── MANIFEST.in                # Include non-Python files
│   ├── LICENSE                    # MIT License
│   ├── README.md                  # PyPI description
│   └── src/
│       ├── cli.py                 # CLI entry point
│       └── ...
```

## 🚀 Publishing Methods

### Method 1: Automated via GitHub Release (Recommended)

1. **Update Version** in `pyproject.toml`:
   ```toml
   version = "0.1.1"
   ```

2. **Commit and Push**:
   ```bash
   git add fuse_backend/pyproject.toml
   git commit -m "Bump version to 0.1.1"
   git push origin main
   ```

3. **Create GitHub Release**:
   ```bash
   # Create and push tag
   git tag v0.1.1
   git push origin v0.1.1
   
   # Or use GitHub UI to create release from tag
   ```

4. **Automated Publishing**: GitHub Actions will automatically:
   - Build the package
   - Run checks
   - Publish to PyPI
   - Upload distribution files to GitHub Release

### Method 2: Manual Test Publishing

For testing before production release:

1. **Trigger Workflow Manually**:
   - Go to GitHub Actions
   - Select "Publish to PyPI" workflow
   - Click "Run workflow"
   - Choose "testpypi" from dropdown
   - Click "Run workflow"

2. **Verify on Test PyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ workflow-automation-platform
   ```

### Method 3: Local Publishing (Not Recommended)

Only use for initial setup or troubleshooting:

```bash
cd fuse_backend

# Install build tools
pip install build twine

# Build package
python -m build

# Check the distribution
twine check dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## ✅ Pre-Publishing Checklist

Before publishing, ensure:

- [ ] **Version updated** in `pyproject.toml`
- [ ] **README.md** is comprehensive and formatted
- [ ] **LICENSE** file exists
- [ ] **All tests pass** locally
- [ ] **.gitignore** excludes build artifacts
- [ ] **Dependencies** are correctly specified
- [ ] **Entry points** (CLI) are configured
- [ ] **MANIFEST.in** includes all necessary files
- [ ] **Tested on Test PyPI** first

## 📝 Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Major (X.0.0)**: Breaking changes
- **Minor (0.X.0)**: New features, backwards compatible
- **Patch (0.0.X)**: Bug fixes

Example progression:
- `0.1.0` - Initial release
- `0.1.1` - Bug fix
- `0.2.0` - New feature
- `1.0.0` - Production ready

## 🔍 Verification

After publishing, verify the package:

### 1. Check PyPI Page
Visit: https://pypi.org/project/workflow-automation-platform/

### 2. Test Installation
```bash
# Create clean environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from PyPI
pip install workflow-automation-platform

# Test CLI
workflow-automation --version
workflow-automation init
workflow-automation start
```

### 3. Check Package Contents
```bash
pip show workflow-automation-platform
pip show -f workflow-automation-platform  # Show all files
```

## 🛠 Troubleshooting

### Issue: "Project name already exists"

**Solution**: Choose a unique name in `pyproject.toml`. Check availability on PyPI.

### Issue: "Invalid distribution file"

**Solution**: Run `twine check dist/*` to identify issues. Common problems:
- Missing `README.md`
- Invalid `pyproject.toml` syntax
- Missing required fields

### Issue: "Trusted publishing not working"

**Solution**:
1. Verify OIDC configuration on PyPI matches GitHub repo exactly
2. Ensure workflow file name matches exactly
3. Check that the release/tag name follows semantic versioning

### Issue: "Package installs but CLI doesn't work"

**Solution**:
1. Verify `[project.scripts]` in `pyproject.toml`
2. Check that `src/cli.py` has correct entry point
3. Reinstall in development mode: `pip install -e .`

## 📊 GitHub Actions Workflow Details

The workflow triggers on:
1. **GitHub Release**: Automatically publishes to PyPI
2. **Manual Dispatch**: Test publishing to Test PyPI

### Workflow Steps:

1. **Checkout**: Fetch repository code
2. **Setup Python**: Install Python 3.11
3. **Install Dependencies**: Build tools and twine
4. **Verify MANIFEST**: Check file inclusion
5. **Build Package**: Create `.tar.gz` and `.whl`
6. **Check Distribution**: Validate with twine
7. **Publish**: Upload to PyPI/Test PyPI
8. **Upload Assets**: Attach dist files to GitHub release

## 🔐 Security Best Practices

1. **Never commit API tokens** to repository
2. **Use trusted publishing** over API tokens when possible
3. **Enable 2FA** on PyPI account
4. **Review GitHub Actions logs** for sensitive data leaks
5. **Rotate credentials** if compromised

## 📚 Additional Resources

- [PyPI Help](https://pypi.org/help/)
- [Python Packaging Guide](https://packaging.python.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [Semantic Versioning](https://semver.org/)

## 🎯 Quick Reference

```bash
# Build package locally
cd fuse_backend && python -m build

# Check package
twine check dist/*

# Test install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ workflow-automation-platform

# Install from PyPI
pip install workflow-automation-platform

# Update package
pip install --upgrade workflow-automation-platform
```

---

**Ready to publish?** Follow Method 1 (GitHub Release) for the smoothest experience! 🚀
