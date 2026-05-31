# EDF Annotations Guide

## Overview

Annotations in EDF files are time-stamped markers that indicate experimental conditions, events, or states during the recording. They're perfect for marking:
- **Eyes open/closed conditions**
- **Task blocks** (baseline, stimulus, response periods)
- **Experimental phases** (rest, task, recovery)
- **Events** (button presses, stimuli presentations)

## Quick Start

```python
from utils import json_to_edf

# Define annotations
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

## Annotation Format

Annotations are specified as a dictionary where:
- **Keys** are the annotation labels (strings)
- **Values** are lists of events, each with:
  - `start`: Time in seconds from the beginning of the recording
  - `duration`: Duration in seconds

```python
{
    "label_name": [
        {"start": <time_seconds>, "duration": <duration_seconds>},
        {"start": <time_seconds>, "duration": <duration_seconds>},
        # ... more events with same label
    ],
    "another_label": [
        {"start": <time_seconds>, "duration": <duration_seconds>}
    ]
}
```

## Examples

### Example 1: Eyes Open/Closed Protocol

```python
annotations = {
    "eyes_open": [
        {"start": 0, "duration": 30},
        {"start": 60, "duration": 30},
        {"start": 120, "duration": 30}
    ],
    "eyes_closed": [
        {"start": 30, "duration": 30},
        {"start": 90, "duration": 30},
        {"start": 150, "duration": 30}
    ]
}
```

### Example 2: Task Blocks

```python
annotations = {
    "baseline": [
        {"start": 0, "duration": 60}
    ],
    "task_1": [
        {"start": 60, "duration": 120}
    ],
    "rest": [
        {"start": 180, "duration": 30}
    ],
    "task_2": [
        {"start": 210, "duration": 120}
    ]
}
```

### Example 3: Multiple Short Events

```python
annotations = {
    "stimulus_A": [
        {"start": 10, "duration": 2},
        {"start": 25, "duration": 2},
        {"start": 40, "duration": 2}
    ],
    "stimulus_B": [
        {"start": 15, "duration": 2},
        {"start": 30, "duration": 2},
        {"start": 45, "duration": 2}
    ],
    "response": [
        {"start": 12, "duration": 0.5},
        {"start": 27, "duration": 0.5},
        {"start": 42, "duration": 0.5}
    ]
}
```

### Example 4: Overlapping Annotations

Annotations can overlap! This is useful for marking concurrent conditions:

```python
annotations = {
    "task_block": [
        {"start": 0, "duration": 120}  # Overall task period
    ],
    "attention_check": [
        {"start": 30, "duration": 5},   # Attention check within task
        {"start": 90, "duration": 5}
    ],
    "high_difficulty": [
        {"start": 60, "duration": 30}   # High difficulty portion of task
    ]
}
```

## Reading Annotations Back

After converting to EDF, you can read annotations back:

```python
import pyedflib

# Open EDF file
edf = pyedflib.EdfReader('output.edf')

# Read all annotations
annot_times, annot_durations, annot_texts = edf.readAnnotations()

# Process annotations
for time, duration, text in zip(annot_times, annot_durations, annot_texts):
    end_time = time + duration
    print(f"{text}: {time:.1f}s - {end_time:.1f}s (duration: {duration:.1f}s)")

edf.close()
```

## Using with Both Functions

### With `json_to_edf()`

```python
from utils import json_to_edf

annotations = {"eyes_open": [{"start": 0, "duration": 60}]}

json_to_edf(
    'recording.json',
    'output.edf',
    subject_name='Subject_01',
    annotations=annotations
)
```

### With `export_to_edf()`

```python
from utils import load_eeg, export_to_edf

# Load data first
metadata, eeg_df, motion_df, ppg_df = load_eeg('recording.json')

# Define annotations
annotations = {"eyes_closed": [{"start": 0, "duration": 60}]}

# Export with annotations
export_to_edf(
    'output.edf',
    metadata,
    eeg_df,
    motion_df,
    ppg_df,
    subject_name='Subject_01',
    annotations=annotations
)
```

## Best Practices

1. **Use descriptive labels**: `"eyes_open"` is better than `"eo"` or `"1"`

2. **Be consistent**: Use the same labels across subjects
   ```python
   # Good
   "eyes_open", "eyes_closed"
   
   # Avoid mixing
   "eyes_open", "EyesClosed", "eyes closed", "EC"
   ```

3. **Use underscores, not spaces**: `"task_block_1"` not `"task block 1"`

4. **Document your protocol**: Keep a separate file describing what each label means

5. **Zero duration is okay**: For instantaneous events like button presses
   ```python
   {"button_press": [{"start": 12.5, "duration": 0}]}
   ```

6. **Check timing**: Make sure annotation times don't exceed recording duration

## Troubleshooting

### Annotations not appearing

Check that you're using EDF+ format (automatic in this library) and that annotations are properly formatted.

### Wrong timestamps

Remember that times are in seconds from the **start of the EDF recording**, not from when you started your experiment. Adjust if needed:

```python
experiment_start_time = 5.0  # Recording started 5 seconds before experiment

annotations = {
    "task": [
        {"start": experiment_start_time + 0, "duration": 60}
    ]
}
```

### Too many annotations

There's no practical limit, but very dense annotations might make the file harder to navigate in some viewers. Consider grouping similar events.

## Compatibility

EDF+ annotations are supported by most EEG analysis tools:
- ✓ MNE-Python (`mne.read_annotations()`)
- ✓ EEGLAB (with BioSig plugin)
- ✓ FieldTrip
- ✓ BrainVision Analyzer
- ✓ Most clinical EEG viewers

## Advanced Usage

### Creating Annotations Programmatically

```python
# Generate repeating pattern
n_trials = 10
trial_duration = 15
rest_duration = 5

annotations = {
    "trial": [],
    "rest": []
}

for i in range(n_trials):
    trial_start = i * (trial_duration + rest_duration)
    rest_start = trial_start + trial_duration
    
    annotations["trial"].append({
        "start": trial_start,
        "duration": trial_duration
    })
    annotations["rest"].append({
        "start": rest_start,
        "duration": rest_duration
    })
```

### Loading Annotations from File

```python
import json

# Save annotations to JSON
with open('protocol.json', 'w') as f:
    json.dump(annotations, f, indent=2)

# Load later
with open('protocol.json', 'r') as f:
    annotations = json.load(f)

json_to_edf('recording.json', 'output.edf', annotations=annotations)
```

## See Also

- `EDF_CONVERSION_README.md` - General conversion guide
- `edf_conversion_examples.ipynb` - Interactive examples
- [EDF+ Specification](https://www.edfplus.info/) - Technical details

