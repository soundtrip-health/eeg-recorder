# EEG JSON to EDF Conversion Tools

Convert custom JSON EEG files from Muse devices to standard European Data Format (EDF) with annotation support.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-BSD-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-19%20passed-brightgreen.svg)](test_edf_conversion.py)

## Features

- ✅ **Multi-channel support**: EEG (4-5 channels), accelerometer (3 axes), gyroscope (3 axes), PPG (3 channels)
- ✅ **Flexible export**: Choose which data types to include
- ✅ **Annotation support**: Add time-stamped markers for experimental conditions
- ✅ **Signal filtering**: Optional 50/60 Hz notch filter
- ✅ **Standard compliant**: Valid EDF+ format compatible with all major EEG tools
- ✅ **Well tested**: 19 comprehensive unit tests (100% passing)
- ✅ **Fully documented**: Complete guides and examples

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd eeg-recorder/analysis

# Install dependencies
pip install -r requirements.txt
```

See [INSTALL.md](INSTALL.md) for detailed instructions.

### Basic Usage

```python
from utils import json_to_edf

# Convert JSON to EDF
json_to_edf('recording.json', 'output.edf', subject_name='Subject_01')
```

### With Annotations

```python
# Define experimental conditions
annotations = {
    "eyes_open": [
        {"start": 0, "duration": 30},
        {"start": 60, "duration": 30}
    ],
    "eyes_closed": [
        {"start": 30, "duration": 30},
        {"start": 90, "duration": 30}
    ]
}

# Convert with annotations
json_to_edf(
    'recording.json',
    'output.edf',
    subject_name='Subject_01',
    annotations=annotations
)
```

## Documentation

| Document | Description |
|----------|-------------|
| **[EDF_CONVERSION_README.md](EDF_CONVERSION_README.md)** | Complete user guide with API reference |
| **[ANNOTATIONS_GUIDE.md](ANNOTATIONS_GUIDE.md)** | How to use annotations for experimental markers |
| **[INSTALL.md](INSTALL.md)** | Installation guide with troubleshooting |
| **[TEST_README.md](TEST_README.md)** | Guide for running and extending tests |
| **[SUMMARY.md](SUMMARY.md)** | Project overview and features |

## Examples

### Python Script

Run the example script:

```bash
python json_to_edf.py
```

See [json_to_edf.py](json_to_edf.py) for multiple examples.

### Jupyter Notebook

Open the interactive notebook:

```bash
jupyter notebook edf_conversion_examples.ipynb
```

See [edf_conversion_examples.ipynb](edf_conversion_examples.ipynb) for step-by-step examples.

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_edf_conversion.py -v

# Run specific test class
pytest test_edf_conversion.py::TestAnnotations -v

# Run with coverage
pytest test_edf_conversion.py --cov=utils --cov-report=html
```

See [TEST_README.md](TEST_README.md) for more testing options.

## API Reference

### `json_to_edf()`

Convert JSON file directly to EDF format.

```python
json_to_edf(
    json_filename,
    output_filename=None,
    subject_name=None,
    include_motion=True,
    include_ppg=True,
    line_freq=60,
    annotations=None
)
```

**Parameters:**
- `json_filename` (str): Path to input JSON file
- `output_filename` (str, optional): Path to output EDF file
- `subject_name` (str, optional): Subject identifier
- `include_motion` (bool): Include accelerometer/gyroscope data
- `include_ppg` (bool): Include PPG data
- `line_freq` (int): Notch filter frequency (50 or 60 Hz, None to disable)
- `annotations` (dict, optional): Time-stamped annotations

### `load_eeg()`

Load EEG data from JSON file.

```python
metadata, eeg_df, motion_df, ppg_df = load_eeg(json_filename, line_freq=60)
```

### `export_to_edf()`

Export loaded data to EDF format.

```python
export_to_edf(
    output_filename,
    metadata,
    eeg_df,
    motion_df=None,
    ppg_df=None,
    subject_name="Unknown",
    include_motion=True,
    include_ppg=True,
    annotations=None
)
```

See [EDF_CONVERSION_README.md](EDF_CONVERSION_README.md) for complete API documentation.

## Use Cases

### Clinical Research
```python
json_to_edf('patient001.json', 'patient001.edf', 
            subject_name='Patient_001',
            include_motion=False,
            include_ppg=False)
```

### Experimental Psychology
```python
annotations = {
    "baseline": [{"start": 0, "duration": 60}],
    "task": [{"start": 60, "duration": 120}],
    "recovery": [{"start": 180, "duration": 60}]
}

json_to_edf('experiment.json', 'experiment.edf', 
            annotations=annotations)
```

### Batch Processing
```python
from pathlib import Path

for json_file in Path('data').glob('*.json'):
    edf_file = json_file.with_suffix('.edf')
    json_to_edf(str(json_file), str(edf_file))
```

## Signal Specifications

| Signal Type | Channels | Rate | Units |
|------------|----------|------|-------|
| EEG | 4-5 | 256 Hz | µV |
| Accelerometer | 3 | 52 Hz | g |
| Gyroscope | 3 | 52 Hz | deg/s |
| PPG | 3 | 64 Hz | au |

## Requirements

- Python 3.8+
- numpy ≥ 2.2.0
- pandas ≥ 2.3.0
- scipy ≥ 1.16.0
- pyedflib ≥ 0.1.42

See [requirements.txt](requirements.txt) for complete list.

## Development

Install development dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

This includes testing tools, Jupyter support, and code quality tools.

## Compatibility

The generated EDF files are compatible with:
- ✅ MNE-Python
- ✅ EEGLAB (with BioSig plugin)
- ✅ FieldTrip
- ✅ BrainVision Analyzer
- ✅ Most clinical EEG viewers

## File Structure

```
analysis/
├── utils.py                           # Core conversion functions
├── json_to_edf.py                     # Example script
├── edf_conversion_examples.ipynb      # Interactive examples
│
├── test_edf_conversion.py             # Test suite (19 tests)
├── pytest.ini                         # Test configuration
│
├── requirements.txt                   # Core dependencies
├── requirements-dev.txt               # Development dependencies
│
├── README.md                          # This file
├── EDF_CONVERSION_README.md           # User guide
├── ANNOTATIONS_GUIDE.md               # Annotation guide
├── TEST_README.md                     # Testing guide
├── INSTALL.md                         # Installation guide
└── SUMMARY.md                         # Project overview
```

## Troubleshooting

### Import Error
```bash
pip install pyedflib
```

### Tests Fail
```bash
pytest test_edf_conversion.py -vv
```

See [INSTALL.md](INSTALL.md) for detailed troubleshooting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest test_edf_conversion.py -v`
6. Submit a pull request

## License

BSD-style license (same as PyEDFlib).

## Acknowledgments

- **PyEDFlib** - EDF file I/O library
- **EDFlib** by Teunis van Beelen - Underlying C library
- **EDF+ specification** - Standard format definition

## Resources

- [PyEDFlib Documentation](https://pyedflib.readthedocs.io/)
- [EDF/EDF+ Specification](https://www.edfplus.info/)
- [MNE-Python](https://mne.tools/) - Python EEG analysis
- [EEGLAB](https://sccn.ucsd.edu/eeglab/) - MATLAB EEG analysis

## Support

For issues, questions, or contributions:
1. Check the documentation files
2. Run tests: `pytest test_edf_conversion.py -v`
3. Open an issue on GitHub (if applicable)

---

**Version**: 1.0  
**Status**: Production Ready ✅  
**Last Updated**: October 2025

