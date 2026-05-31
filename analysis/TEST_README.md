# EDF Conversion Test Suite

Comprehensive unit tests for the JSON to EDF conversion functionality using pytest.

## Running Tests

### Run all tests

```bash
pytest test_edf_conversion.py -v
```

### Run specific test class

```bash
# Test basic conversion
pytest test_edf_conversion.py::TestBasicConversion -v

# Test annotations
pytest test_edf_conversion.py::TestAnnotations -v

# Test signal quality
pytest test_edf_conversion.py::TestSignalQuality -v

# Test edge cases
pytest test_edf_conversion.py::TestEdgeCases -v

# Test integration
pytest test_edf_conversion.py::TestIntegration -v
```

### Run specific test

```bash
pytest test_edf_conversion.py::TestAnnotations::test_json_to_edf_with_annotations -v
```

### Run with coverage (if pytest-cov installed)

```bash
pip install pytest-cov
pytest test_edf_conversion.py --cov=utils --cov-report=html
```

### Run with quiet output

```bash
pytest test_edf_conversion.py -q
```

### Run and stop on first failure

```bash
pytest test_edf_conversion.py -x
```

## Test Structure

### TestBasicConversion (4 tests)
Tests core conversion functionality without annotations:
- `test_json_to_edf_all_data` - Convert with all data types (EEG, motion, PPG)
- `test_json_to_edf_eeg_only` - Convert only EEG channels
- `test_json_to_edf_no_filtering` - Conversion without notch filter
- `test_export_to_edf_separate_load` - Export with separately loaded data

### TestAnnotations (6 tests)
Tests annotation functionality:
- `test_json_to_edf_with_annotations` - Basic annotation support
- `test_export_to_edf_with_annotations` - Annotations with export_to_edf
- `test_no_annotations` - Conversion without annotations
- `test_annotation_timing` - Verify annotation timing accuracy
- `test_multiple_events_same_label` - Multiple events with same label
- `test_overlapping_annotations` - Overlapping time periods

### TestSignalQuality (4 tests)
Tests signal data integrity:
- `test_signal_sample_rates` - Verify correct sampling rates (256/52/64 Hz)
- `test_signal_labels` - Check all channel labels present
- `test_physical_dimensions` - Verify units (uV, g, deg/s, au)
- `test_data_not_empty` - Ensure signals contain data

### TestEdgeCases (4 tests)
Tests edge cases and error handling:
- `test_empty_annotations` - Empty annotation dictionary
- `test_zero_duration_annotation` - Instantaneous events (duration=0)
- `test_subject_name_with_spaces` - Subject names with spaces
- `test_automatic_output_filename` - Auto-generated filenames

### TestIntegration (1 test)
End-to-end integration test:
- `test_complete_workflow` - Full workflow with all features

## Test Coverage

The test suite covers:
- ✅ Basic JSON to EDF conversion
- ✅ Selective data export (EEG only, with/without motion/PPG)
- ✅ Notch filtering (50/60 Hz and disabled)
- ✅ Annotation support (multiple labels, events, timings)
- ✅ Signal quality (sample rates, labels, units)
- ✅ Edge cases (empty annotations, zero duration, special characters)
- ✅ Data integrity (correct channel count, non-empty signals)
- ✅ Complete workflows

**Total: 19 tests, 100% passing**

## Fixtures

The test suite uses pytest fixtures for test data:
- `test_json_file` - Path to test JSON file
- `output_dir` - Temporary directory for outputs (auto-cleanup)
- `sample_annotations` - Basic eyes open/closed annotations
- `complex_annotations` - Multi-phase task annotations

## Requirements

```bash
pip install pytest pyedflib pandas numpy scipy
```

## Continuous Integration

To set up CI/CD, add to your workflow:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install pytest pyedflib pandas numpy scipy
      - name: Run tests
        run: |
          cd analysis
          pytest test_edf_conversion.py -v
```

## Troubleshooting

### Test file not found

Make sure you're in the `analysis` directory:
```bash
cd analysis
pytest test_edf_conversion.py -v
```

### Module import errors

Make sure `utils.py` is in the same directory and activate the virtual environment:
```bash
source .venv/bin/activate
```

### Data file not found

The tests require `data/MuseS-5743_2025-10-17T19_30_11.142Z.json` to exist.

### Warnings about physical min/max

These warnings from pyedflib are expected and don't indicate test failures. They can be suppressed in `pytest.ini`.

## Adding New Tests

To add new tests:

1. Add test method to appropriate class:
```python
def test_new_feature(self, test_json_file, output_dir):
    """Test description"""
    output_file = output_dir / "test_new.edf"
    
    result = json_to_edf(
        test_json_file,
        str(output_file),
        subject_name='Test'
    )
    
    assert os.path.exists(result)
    # Add assertions
```

2. Run the new test:
```bash
pytest test_edf_conversion.py::TestClassName::test_new_feature -v
```

## Best Practices

1. **Use descriptive test names** - Name should explain what is being tested
2. **One assertion focus per test** - Test one thing at a time
3. **Use fixtures** - Reuse common setup code
4. **Clean up** - Use `tmp_path` fixture for automatic cleanup
5. **Test edge cases** - Empty inputs, zero values, special characters
6. **Document tests** - Add docstrings explaining test purpose

## Performance

Test suite typically runs in ~2 minutes on modern hardware:
- Basic conversion tests: ~30s
- Annotation tests: ~45s
- Signal quality tests: ~30s
- Edge cases: ~10s
- Integration test: ~5s

To speed up tests, you can:
- Run tests in parallel: `pytest -n auto` (requires pytest-xdist)
- Skip slow tests: `pytest -m "not slow"`
- Run subset of tests: `pytest test_edf_conversion.py::TestAnnotations`

