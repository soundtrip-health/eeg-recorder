# JSON to EDF Conversion Guide

This guide explains how to convert custom JSON EEG files from Muse devices to the standard European Data Format (EDF).

## Quick Start

```python
from utils import json_to_edf

# Convert JSON to EDF
json_to_edf('data/recording.json', 'output.edf', patient_name='Subject_01')
```

## Features

The conversion supports:
- **EEG channels**: TP9, AF7, AF8, TP10, AUX (256 Hz)
- **Accelerometer**: 3-axis acceleration data (52 Hz)
- **Gyroscope**: 3-axis angular velocity data (52 Hz)
- **PPG**: Photoplethysmograph channels (64 Hz)
- **Notch filtering**: Optional 50/60 Hz line noise removal
- **Annotations**: Time-stamped markers for experimental conditions (eyes open/closed, task blocks, etc.)

## Function Reference

### `json_to_edf()`

Convenience function to convert JSON files directly to EDF format.

**Signature:**
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
- `output_filename` (str, optional): Path to output EDF file. If None, uses same name as JSON with .edf extension
- `subject_name` (str, optional): Patient/subject identifier. If None, extracted from metadata
- `include_motion` (bool): Include accelerometer and gyroscope data (default: True)
- `include_ppg` (bool): Include PPG data (default: True)
- `line_freq` (int): Line frequency for notch filter - 50 or 60 Hz. Set to None to disable filtering
- `annotations` (dict, optional): Dictionary of annotations with format:
  `{"label": [{"start": time_in_seconds, "duration": duration_in_seconds}, ...], ...}`

**Returns:**
- str: Path to the created EDF file

**Example:**
```python
output = json_to_edf(
    'data/recording.json',
    'data/subject01.edf',
    patient_name='Subject_01',
    include_motion=True,
    include_ppg=True,
    line_freq=60  # Use 50 for Europe
)
```

### `load_eeg()`

Load EEG data from JSON file into pandas DataFrames.

**Signature:**
```python
metadata, eeg_df, motion_df, ppg_df = load_eeg(json_filename, line_freq=60)
```

**Parameters:**
- `json_filename` (str): Path to input JSON file
- `line_freq` (int): Line frequency for notch filter (50 or 60 Hz, None to disable)

**Returns:**
- `metadata` (dict): Device metadata and electrode names
- `eeg_df` (DataFrame): EEG data with electrode columns, indexed by relative time
- `motion_df` (DataFrame): Accelerometer and gyroscope data (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z)
- `ppg_df` (DataFrame): PPG channels data

**Example:**
```python
metadata, eeg_df, motion_df, ppg_df = load_eeg('data/recording.json', line_freq=60)

print(f"EEG channels: {list(eeg_df.columns)}")
print(f"EEG shape: {eeg_df.shape}")
print(f"Duration: {eeg_df.index[-1]:.2f} seconds")
```

### `export_to_edf()`

Export loaded data to EDF format (for advanced use cases).

**Signature:**
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

**Parameters:**
- `output_filename` (str): Path to output EDF file
- `metadata` (dict): Metadata dictionary from `load_eeg()`
- `eeg_df` (DataFrame): EEG data
- `motion_df` (DataFrame, optional): Motion data
- `ppg_df` (DataFrame, optional): PPG data
- `subject_name` (str): Subject identifier
- `include_motion` (bool): Include motion data (default: True)
- `include_ppg` (bool): Include PPG data (default: True)
- `annotations` (dict, optional): Dictionary of annotations (see `json_to_edf()` for format)

**Returns:**
- str: Path to the created EDF file

**Example:**
```python
# Load data
metadata, eeg_df, motion_df, ppg_df = load_eeg('data/recording.json')

# Export with custom settings
export_to_edf(
    'data/custom.edf',
    metadata,
    eeg_df,
    motion_df,
    ppg_df,
    patient_name='Custom_Subject',
    include_motion=True,
    include_ppg=False  # Exclude PPG
)
```

## Common Use Cases

### 1. Convert Everything
```python
json_to_edf('recording.json', 'output.edf', patient_name='Subject01')
```

### 2. EEG Only
```python
json_to_edf('recording.json', 'eeg_only.edf', 
            patient_name='Subject01',
            include_motion=False, 
            include_ppg=False)
```

### 3. Custom Filtering (50 Hz line frequency)
```python
json_to_edf('recording.json', 'output.edf', 
            patient_name='Subject01',
            line_freq=50)  # For European power grid
```

### 4. No Filtering
```python
json_to_edf('recording.json', 'output.edf', 
            patient_name='Subject01',
            line_freq=None)  # Disable notch filter
```

### 5. With Annotations
```python
annotations = {
    "eyes_open": [
        {"start": 0, "duration": 30},
        {"start": 60, "duration": 30}
    ],
    "eyes_closed": [
        {"start": 30, "duration": 30},
        {"start": 90, "duration": 30}
    ],
    "task_block_1": [
        {"start": 120, "duration": 60}
    ]
}

json_to_edf('recording.json', 'output.edf', 
            subject_name='Subject01',
            annotations=annotations)
```

### 6. Batch Conversion
```python
from pathlib import Path

data_dir = Path('data')
for json_file in data_dir.glob('*.json'):
    output_file = json_file.with_suffix('.edf')
    json_to_edf(str(json_file), str(output_file))
```

## Reading EDF Files

To read back the EDF files:

```python
import pyedflib
import numpy as np

# Open file
edf = pyedflib.EdfReader('output.edf')

# Get information
n_channels = edf.signals_in_file
labels = edf.getSignalLabels()
duration = edf.getFileDuration()

# Read a specific channel
channel_idx = 0  # First channel (TP9)
signal_data = edf.readSignal(channel_idx)
sample_rate = edf.getSampleFrequency(channel_idx)

# Read annotations
annot_times, annot_durations, annot_texts = edf.readAnnotations()
for time, duration, text in zip(annot_times, annot_durations, annot_texts):
    print(f"{time:.1f}s - {time+duration:.1f}s: {text}")

# Close file
edf.close()
```

## EDF Format Details

The generated EDF files follow the EDF+ specification:

- **File Type**: EDF+ (EDF Plus)
- **Digital Resolution**: 16-bit (±32767)
- **Physical Units**:
  - EEG: microvolts (uV)
  - Accelerometer: g (gravity)
  - Gyroscope: deg/s (degrees per second)
  - PPG: au (arbitrary units)

## Troubleshooting

### Import Error: No module named 'pyedflib'

Install pyedflib:
```bash
pip install pyedflib
```

### Warnings about physical min/max truncation

These are informational warnings. EDF format limits physical min/max values to 8 characters. The conversion automatically rounds values to fit, with minimal precision loss (typically < 0.01%).

### Different sampling rates

The EDF format natively supports different sampling rates for different channels. Each channel maintains its original sampling rate:
- EEG: 256 Hz
- Motion: 52 Hz
- PPG: 64 Hz

## Additional Resources

- [PyEDFlib Documentation](https://pyedflib.readthedocs.io/en/latest/)
- [EDF/EDF+ Specification](https://www.edfplus.info/)
- Example notebook: `edf_conversion_examples.ipynb`
- Example script: `json_to_edf.py`

