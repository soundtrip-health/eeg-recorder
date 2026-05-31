# Installation Guide

This guide explains how to install and set up the EDF conversion tools.

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd eeg-recorder/analysis
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# If you're developing/testing, also install development dependencies
pip install -r requirements-dev.txt
```

### 4. Verify Installation

```bash
# Run tests to verify everything is working
pytest test_edf_conversion.py -v
```

## Installation Options

### Option 1: Core Dependencies Only (Recommended for Production)

Install only what's needed to run the conversion tools:

```bash
pip install -r requirements.txt
```

**Includes:**
- numpy, pandas, scipy (data processing)
- pyedflib (EDF file support)
- ordpy, antropy (analysis tools)

**Use for:**
- Converting JSON files to EDF
- Running the conversion in production
- Minimal installations

### Option 2: Full Development Setup

Install everything for development, testing, and analysis:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

**Includes all core dependencies plus:**
- pytest, pytest-cov (testing)
- Jupyter notebook support
- matplotlib, seaborn (visualization)
- black, flake8, mypy (code quality)

**Use for:**
- Development
- Running tests
- Using Jupyter notebooks
- Contributing to the project

### Option 3: Minimal Installation

If you only need specific functionality:

```bash
# Just EDF conversion (no complexity analysis)
pip install numpy pandas scipy pyedflib

# Add testing
pip install pytest
```

## Dependency Overview

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | ≥2.2.0 | Array operations |
| pandas | ≥2.3.0 | Data manipulation |
| scipy | ≥1.16.0 | Signal processing |
| pyedflib | ≥0.1.42 | EDF file I/O |
| ordpy | ≥1.2.0 | Ordinal patterns |
| antropy | ≥0.1.9 | Entropy measures |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | ≥8.4.0 | Testing framework |
| pytest-cov | ≥4.0.0 | Test coverage |
| jupyter | - | Notebook interface |
| matplotlib | ≥3.8.0 | Plotting |
| black | ≥24.0.0 | Code formatting |

## Platform-Specific Notes

### macOS

Python 3.8+ should work. Install via Homebrew if needed:

```bash
brew install python@3.11
```

### Linux

Most distributions come with Python 3. Install pip if needed:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv

# Fedora/RHEL
sudo dnf install python3-pip
```

### Windows

Download Python from [python.org](https://python.org) (3.8 or later).

Use Command Prompt or PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Troubleshooting

### Issue: "No module named 'pyedflib'"

**Solution:**
```bash
pip install pyedflib
```

### Issue: "Microsoft Visual C++ is required" (Windows)

**Solution:**
Install Microsoft C++ Build Tools from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### Issue: "Permission denied" when installing

**Solution:**
Use a virtual environment (recommended) or install with `--user`:
```bash
pip install --user -r requirements.txt
```

### Issue: scipy/numpy compilation errors

**Solution:**
Use pre-built wheels (usually automatic) or install system packages:

```bash
# macOS
brew install openblas

# Ubuntu/Debian  
sudo apt-get install libopenblas-dev liblapack-dev

# Then reinstall
pip install --upgrade scipy numpy
```

### Issue: Tests fail

**Solution:**
1. Ensure test data file exists: `data/MuseS-5743_2025-10-17T19_30_11.142Z.json`
2. Verify all dependencies installed: `pip list`
3. Run tests with verbose output: `pytest test_edf_conversion.py -vv`

## Updating Dependencies

### Update all packages to latest versions

```bash
pip install --upgrade -r requirements.txt
```

### Update specific package

```bash
pip install --upgrade pyedflib
```

### Check for outdated packages

```bash
pip list --outdated
```

## Uninstallation

To completely remove the installation:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment directory
rm -rf .venv

# Or on Windows
rmdir /s .venv
```

## Docker Installation (Optional)

For a containerized setup:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "json_to_edf.py"]
```

Build and run:

```bash
docker build -t edf-converter .
docker run -v $(pwd)/data:/app/data edf-converter
```

## Verifying Installation

Run this quick test:

```python
from utils import json_to_edf
import pyedflib

print("✓ All imports successful!")
print(f"pyedflib version: {pyedflib.__version__}")
```

## Next Steps

After installation:

1. **Read the documentation**
   - `EDF_CONVERSION_README.md` - User guide
   - `ANNOTATIONS_GUIDE.md` - Annotation features
   - `TEST_README.md` - Running tests

2. **Try the examples**
   - Run `python json_to_edf.py`
   - Open `edf_conversion_examples.ipynb` in Jupyter

3. **Run the tests**
   - `pytest test_edf_conversion.py -v`

4. **Convert your data**
   - See examples in documentation
   - Start with `json_to_edf('your_file.json', 'output.edf')`

## Getting Help

- Check documentation files in this directory
- Review example scripts and notebooks
- Run tests to verify setup: `pytest test_edf_conversion.py -v`
- Check GitHub issues (if applicable)

## Version Requirements

- **Python**: 3.8 or later (3.11+ recommended)
- **pip**: 20.0 or later (for dependency resolution)
- **OS**: macOS, Linux, or Windows 10+

## License

See LICENSE file for details.

