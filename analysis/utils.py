from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import numpy as np
from scipy import signal
from scipy.signal import hilbert 
#from lempel_ziv_complexity import lempel_ziv_complexity
import ordpy
import antropy
import pyedflib
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import mne

EEG_FS = 256
MOT_FS = 52
PPG_FS = 64
EEG_DT = 1 / EEG_FS
MOT_DT = 1 / MOT_FS
PPG_DT = 1 / PPG_FS

def _is_jsonl_file(filename):
    """Check if file is JSONL format (line-delimited JSON) vs single JSON object."""
    with open(filename) as fp:
        first_char = fp.read(1)
        return first_char == '{'


def _load_jsonl(filename):
    """Load JSONL file and return records grouped by type."""
    eeg_records = []
    gyro_records = []
    accel_records = []
    ppg_records = []
    
    with open(filename) as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            record_type = record.get('type')
            if record_type == 'eeg':
                eeg_records.append(record)
            elif record_type == 'gyro':
                gyro_records.append(record)
            elif record_type == 'accel':
                accel_records.append(record)
            elif record_type == 'ppg':
                ppg_records.append(record)
    
    return eeg_records, gyro_records, accel_records, ppg_records


def _load_eeg_from_jsonl(filename, line_freq=60):
    """Load EEG data from JSONL format file."""
    eeg_records, gyro_records, accel_records, ppg_records = _load_jsonl(filename)
    
    # Default electrode names for JSONL format (Muse headband standard)
    default_electrode_names = {0: 'TP9', 1: 'AF7', 2: 'AF8', 3: 'TP10'}
    
    # Build EEG DataFrame
    dfs = []
    if eeg_records:
        # Sort by index to ensure proper ordering
        eeg_records.sort(key=lambda x: (x['index'], x['electrode']))
        seq_start = min(r['index'] for r in eeg_records)
        
        for e in eeg_records:
            tmpdf = pd.DataFrame([{"electrode": e["electrode"], "value": s} 
                                  for s in e["samples"]])
            relseq_time = (e["index"] - seq_start) * EEG_DT * 12
            tmpdf["reltime"] = [EEG_DT * i + relseq_time for i in range(len(e["samples"]))]
            dfs.append(tmpdf)
        
        eeg_df = pd.concat(dfs).pivot(index="reltime", columns="electrode", values="value")
        eeg_df.rename(columns=default_electrode_names, inplace=True)
        
        # Interpolate NaN gaps from dropped packets (filtfilt cannot handle NaN)
        if eeg_df.isna().any().any():
            n_nan = eeg_df.isna().sum().sum()
            n_total = eeg_df.size
            print(f"Warning: {n_nan}/{n_total} NaN values in EEG data ({100*n_nan/n_total:.2f}%), interpolating")
            eeg_df = eeg_df.interpolate(method='linear', limit_direction='both')
            eeg_df = eeg_df.ffill().bfill()
        
        # Notch-filter EEG
        if line_freq:
            b, a = signal.iirnotch(line_freq, Q=30, fs=EEG_FS)
            for e in eeg_df.columns:
                eeg_df[e] = signal.filtfilt(b, a, eeg_df[e])
    else:
        eeg_df = pd.DataFrame()
    
    # Build motion DataFrame
    dfs = []
    if accel_records and gyro_records:
        # Sort and pair accel/gyro by sequenceId
        accel_records.sort(key=lambda x: x.get('sequenceId', x.get('index', 0)))
        gyro_records.sort(key=lambda x: x.get('sequenceId', x.get('index', 0)))
        
        # Build lookup by sequenceId
        gyro_by_seq = {g.get('sequenceId', g.get('index')): g for g in gyro_records}
        
        seq_start = accel_records[0].get('sequenceId', accel_records[0].get('index', 0))
        
        for a in accel_records:
            seq_id = a.get('sequenceId', a.get('index'))
            g = gyro_by_seq.get(seq_id)
            if g is None:
                continue
            
            adf = pd.json_normalize(a["samples"]).rename(columns=dict(x="acc_x", y="acc_y", z="acc_z"))
            gdf = pd.json_normalize(g["samples"]).rename(columns=dict(x="gyr_x", y="gyr_y", z="gyr_z"))
            tmpdf = pd.concat((adf, gdf), axis=1)
            relseq_time = (seq_id - seq_start) * MOT_DT * 3
            tmpdf["reltime"] = [MOT_DT * i + relseq_time for i in range(len(a["samples"]))]
            dfs.append(tmpdf)
        
        motion_df = pd.concat(dfs).set_index("reltime") if dfs else pd.DataFrame()
    else:
        motion_df = pd.DataFrame()
    
    # Build PPG DataFrame
    dfs = []
    if ppg_records:
        ppg_records.sort(key=lambda x: (x['index'], x['ppgChannel']))
        seq_start = min(r['index'] for r in ppg_records)
        
        for p in ppg_records:
            tmpdf = pd.DataFrame([{"channel": p["ppgChannel"], "ppg": s} 
                                  for s in p["samples"]])
            relseq_time = (p["index"] - seq_start) * PPG_DT * 6
            tmpdf["reltime"] = [PPG_DT * i + relseq_time for i in range(len(p["samples"]))]
            dfs.append(tmpdf)
        
        ppg_df = pd.concat(dfs).pivot(index="reltime", columns="channel", values="ppg")
        ppg_df.rename(columns={k: f"ppg{k}" for k in ppg_df.columns}, inplace=True)
        
        # Interpolate NaN gaps from dropped packets
        if ppg_df.isna().any().any():
            n_nan = ppg_df.isna().sum().sum()
            n_total = ppg_df.size
            print(f"Warning: {n_nan}/{n_total} NaN values in PPG data ({100*n_nan/n_total:.2f}%), interpolating")
            ppg_df = ppg_df.interpolate(method='linear', limit_direction='both')
            ppg_df = ppg_df.ffill().bfill()
    else:
        ppg_df = pd.DataFrame()
    
    # Create minimal metadata for JSONL files
    metadata = {
        'electrodeNames': list(default_electrode_names.values()),
        'deviceName': 'Unknown',
        'hw': 'Unknown',
        'fw': 'Unknown',
    }
    
    return metadata, eeg_df, motion_df, ppg_df


def load_eeg(json_filename, line_freq=60):
    """
    Load EEG data from JSON or JSONL file.
    
    Supports two formats:
    1. Single JSON object with nested 'eeg', 'accel', 'gyro', 'ppg' arrays
    2. JSONL (line-delimited JSON) with each line containing a record with 'type' field
    
    Parameters:
    -----------
    json_filename : str
        Path to input JSON or JSONL file
    line_freq : int, optional
        Line frequency for notch filter (50 or 60 Hz). Set to None to disable filtering.
        
    Returns:
    --------
    tuple : (metadata, eeg_df, motion_df, ppg_df)
    """
    # Check if file is JSONL format
    if _is_jsonl_file(json_filename):
        # Peek at first line to determine format
        with open(json_filename) as fp:
            first_line = fp.readline().strip()
            try:
                first_obj = json.loads(first_line)
                # If first object has 'type' field, it's the new JSONL streaming format
                if 'type' in first_obj:
                    return _load_eeg_from_jsonl(json_filename, line_freq)
            except json.JSONDecodeError:
                pass
    
    # Original JSON format handling
    with open(json_filename) as fp:
        jsn = json.load(fp)
    
    dfs = []
    assert jsn["eeg"][0][0]["timestamp"] == jsn["eeg"][1][0]["timestamp"]
    assert jsn["eeg"][0][0]["index"] == jsn["eeg"][1][0]["index"]
    # Should we use the eeg timestamp delta from start_ts? (It's about 40ms)
    print((jsn["start_ts"] - jsn["eeg"][0][0]["timestamp"]) / 1000)
    seq_start = jsn["eeg"][0][0]["index"]
    for chan in jsn["eeg"]:
        for e in chan:
            tmpdf = pd.DataFrame([{"electrode": e["electrode"], "value": s,} 
                                  for i, s in enumerate(e["samples"])])
            relseq_time = (e["index"] - seq_start) * EEG_DT * 12
            tmpdf["reltime"] = [EEG_DT * i + relseq_time for i in range(12)]
            dfs.append(tmpdf)
    eeg_df = pd.concat(dfs).pivot(index="reltime", columns="electrode", values="value")
    electrode_name_map = {i: n for i, n in enumerate(jsn['metadata']['electrodeNames'])}
    eeg_df.rename(columns=electrode_name_map, inplace=True)
    
    # notch-filter eeg
    if line_freq:
        b, a = signal.iirnotch(line_freq, Q=30, fs=EEG_FS)
        for e in eeg_df.columns:
            eeg_df[e] = signal.filtfilt(b, a, eeg_df[e])
    
    dfs = []
    #assert jsn["gyro"][0]["sequenceId"] == jsn["accel"][0]["sequenceId"]
    seq_start = jsn["accel"][0]["sequenceId"]
    for a, g in zip(jsn['accel'], jsn['gyro']):
        adf = pd.json_normalize(a["samples"]).rename(columns=dict(x="acc_x", y="acc_y", z="acc_z"))
        gdf = pd.json_normalize(g["samples"]).rename(columns=dict(x="gyr_x", y="gyr_y", z="gyr_z"))
        tmpdf = pd.concat((adf, gdf), axis=1)
        relseq_time = (a["sequenceId"] - seq_start) * MOT_DT * 3
        tmpdf["reltime"] = [MOT_DT * i + relseq_time for i in range(3)]
        dfs.append(tmpdf)
        #tmpdf['samp_offset'] = [samp_offset for i in tmpdf.index]
        #tmpdf['start'] = jsn["start_ts"]
    motion_df = pd.concat(dfs).set_index("reltime")
    
    dfs = []
    # all timestamps are identical for ppg. And they lead the global start_ts by a bit.
    print((jsn["start_ts"] - jsn["ppg"][0]["timestamp"]) / 1000)
    seq_start = jsn["ppg"][0]["index"]
    for p in jsn["ppg"]:
        tmpdf = pd.DataFrame([{"channel": p["ppgChannel"], "ppg": s,} 
                              for i, s in enumerate(p["samples"])])
        relseq_time = (p["index"] - seq_start) * PPG_DT * 6
        tmpdf["reltime"] = [PPG_DT * i + relseq_time for i in range(6)]
        dfs.append(tmpdf)
    ppg_df = pd.concat(dfs).pivot(index="reltime", columns="channel", values="ppg")
    ppg_df.rename(columns={k: f"ppg{k}" for k in ppg_df.columns}, inplace=True)
    
    return jsn['metadata'], eeg_df, motion_df, ppg_df


def _get_physical_range(data, default_range):
    """
    Get physical min/max for EDF, ensuring valid range.
    
    Uses the larger of the actual data range or the default range,
    and ensures physical_max > physical_min.
    
    Parameters
    ----------
    data : array-like
        Signal data
    default_range : tuple
        (min, max) default physical range for this signal type
        
    Returns
    -------
    tuple : (physical_min, physical_max)
    """
    default_min, default_max = default_range
    
    # Use nanmin/nanmax to handle any residual NaN values
    if np.all(np.isnan(data)):
        return round(default_min, 4), round(default_max, 4)
    
    data_min = float(np.nanmin(data))
    data_max = float(np.nanmax(data))
    
    # Use the larger of actual range or default range
    physical_min = min(data_min, default_min)
    physical_max = max(data_max, default_max)
    
    # Ensure we have a valid range (physical_max > physical_min)
    if physical_max <= physical_min:
        center = (physical_max + physical_min) / 2
        half_range = max(abs(default_max - default_min) / 2, 1.0)
        physical_min = center - half_range
        physical_max = center + half_range
    
    return round(physical_min, 4), round(physical_max, 4)


# Physical range defaults for Muse sensors
# These cover the typical operating ranges with some margin
MUSE_EEG_RANGE = (-1000.0, 1000.0)      # μV - Muse EEG typical range
MUSE_ACCEL_RANGE = (-4.0, 4.0)           # g - Muse accelerometer range
MUSE_GYRO_RANGE = (-1000.0, 1000.0)      # deg/s - Muse gyroscope range
MUSE_PPG_RANGE = (0.0, 65535.0)          # arbitrary units - PPG sensor range


def export_to_edf(output_filename, metadata, eeg_df, motion_df=None, ppg_df=None, 
                  subject_name="Unknown", include_motion=True, include_ppg=True,
                  annotations=None):
    """
    Export EEG data (and optionally motion/PPG data) to EDF format.
    
    Parameters:
    -----------
    output_filename : str
        Path to output EDF file
    metadata : dict
        Metadata dictionary from load_eeg containing device info and electrode names
    eeg_df : pd.DataFrame
        EEG data DataFrame with electrode columns (from load_eeg)
    motion_df : pd.DataFrame, optional
        Motion data DataFrame with acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z columns
    ppg_df : pd.DataFrame, optional
        PPG data DataFrame with ppg channels
    subject_name : str, optional
        Patient/subject identifier (default: "Unknown")
    include_motion : bool, optional
        Whether to include accelerometer and gyroscope data (default: True)
    include_ppg : bool, optional
        Whether to include PPG data (default: True)
    annotations : dict, optional
        Dictionary of annotations with format:
        {"label": [{"start": time_in_seconds, "duration": duration_in_seconds}, ...], ...}
        Example: {"eyes_open": [{"start": 0, "duration": 15}], 
                  "eyes_closed": [{"start": 15, "duration": 15}]}
        
    Returns:
    --------
    str : Path to the created EDF file
    """
    
    # Prepare signal list and data
    signals = []
    signal_data = []
    
    # Add EEG channels (values are in microvolts)
    eeg_channels = [col for col in eeg_df.columns]
    for chan in eeg_channels:
        chan_data = eeg_df[chan].values.astype(np.float64)
        phys_min, phys_max = _get_physical_range(chan_data, MUSE_EEG_RANGE)
        
        signal_dict = {
            'label': chan,
            'dimension': 'uV',
            'sample_rate': EEG_FS,
            'physical_max': phys_max,
            'physical_min': phys_min,
            'digital_max': 32767,
            'digital_min': -32768,
            'transducer': 'EEG electrode',
            'prefilter': 'HP:0.1Hz LP:100Hz N:60Hz'
        }
        signals.append(signal_dict)
        signal_data.append(chan_data)
    
    # Add motion channels (accelerometer and gyroscope) if requested
    if include_motion and motion_df is not None:
        motion_channels = ['acc_x', 'acc_y', 'acc_z', 'gyr_x', 'gyr_y', 'gyr_z']
        for chan in motion_channels:
            if chan in motion_df.columns:
                chan_data = motion_df[chan].values.astype(np.float64)
                
                # Determine units, transducer type, and physical range
                if chan.startswith('acc'):
                    dimension = 'g'
                    transducer = 'Accelerometer'
                    phys_min, phys_max = _get_physical_range(chan_data, MUSE_ACCEL_RANGE)
                else:
                    dimension = 'deg/s'
                    transducer = 'Gyroscope'
                    phys_min, phys_max = _get_physical_range(chan_data, MUSE_GYRO_RANGE)
                
                signal_dict = {
                    'label': chan,
                    'dimension': dimension,
                    'sample_rate': MOT_FS,
                    'physical_max': phys_max,
                    'physical_min': phys_min,
                    'digital_max': 32767,
                    'digital_min': -32768,
                    'transducer': transducer,
                    'prefilter': ''
                }
                signals.append(signal_dict)
                signal_data.append(chan_data)
    
    # Add PPG channels if requested
    if include_ppg and ppg_df is not None:
        ppg_channels = [col for col in ppg_df.columns]
        for chan in ppg_channels:
            chan_data = ppg_df[chan].values.astype(np.float64)
            phys_min, phys_max = _get_physical_range(chan_data, MUSE_PPG_RANGE)
            
            signal_dict = {
                'label': chan,
                'dimension': 'au',
                'sample_rate': PPG_FS,
                'physical_max': phys_max,
                'physical_min': phys_min,
                'digital_max': 32767,
                'digital_min': -32768,
                'transducer': 'PPG sensor',
                'prefilter': ''
            }
            signals.append(signal_dict)
            signal_data.append(chan_data)
    
    # Create EDF file
    edf_file = pyedflib.EdfWriter(output_filename, len(signals), file_type=pyedflib.FILETYPE_EDFPLUS)
    
    # Set file header information
    device_name = metadata.get('deviceName', 'Unknown').replace('-', '_')  # Replace dashes
    recording_date = datetime.now()  # Use current time or parse from metadata if available
    hw_version = metadata.get('hw', 'Unknown')
    fw_version = metadata.get('fw', 'Unknown')
    
    edf_file.setPatientName(subject_name)
    edf_file.setPatientCode(subject_name)
    # Keep equipment string short and ASCII-compliant (max 80 chars total for all fields)
    edf_file.setEquipment(f"{device_name}_HW{hw_version}_FW{fw_version}")
    edf_file.setAdmincode('')  # Keep empty to save space
    edf_file.setTechnician('')  # Keep empty to save space
    edf_file.setRecordingAdditional('')  # Keep empty to save space
    edf_file.setStartdatetime(recording_date)
    
    # Set signal headers
    for i, signal_dict in enumerate(signals):
        edf_file.setLabel(i, signal_dict['label'])
        edf_file.setPhysicalDimension(i, signal_dict['dimension'])
        edf_file.setSamplefrequency(i, signal_dict['sample_rate'])
        edf_file.setPhysicalMaximum(i, signal_dict['physical_max'])
        edf_file.setPhysicalMinimum(i, signal_dict['physical_min'])
        edf_file.setDigitalMaximum(i, signal_dict['digital_max'])
        edf_file.setDigitalMinimum(i, signal_dict['digital_min'])
        edf_file.setTransducer(i, signal_dict['transducer'])
        edf_file.setPrefilter(i, signal_dict['prefilter'])
    
    # Replace any remaining NaN/Inf with 0 (pyedflib cannot handle them)
    for i in range(len(signal_data)):
        mask = ~np.isfinite(signal_data[i])
        if mask.any():
            print(f"Warning: replacing {mask.sum()} non-finite values in channel {signals[i]['label']}")
            signal_data[i] = np.where(mask, 0.0, signal_data[i])
    
    # Write signals to file
    edf_file.writeSamples(signal_data)
    
    # Write annotations if provided
    if annotations:
        for label, events in annotations.items():
            for event in events:
                onset = event.get('start', 0)
                duration = event.get('duration', 0)
                # Write annotation with onset time, duration, and label
                edf_file.writeAnnotation(onset, duration, label)
    
    # Close file
    edf_file.close()
    
    return output_filename


def json_to_edf(json_filename, output_filename=None, subject_name=None, 
                include_motion=True, include_ppg=True, line_freq=60, annotations=None):
    """
    Convenience function to convert a JSON EEG file directly to EDF format.
    
    Parameters:
    -----------
    json_filename : str
        Path to input JSON file
    output_filename : str, optional
        Path to output EDF file. If None, uses same name as JSON file with .edf extension
    subject_name : str, optional
        Patient/subject identifier. If None, extracted from JSON metadata or uses "Unknown"
    include_motion : bool, optional
        Whether to include accelerometer and gyroscope data (default: True)
    include_ppg : bool, optional
        Whether to include PPG data (default: True)
    line_freq : int, optional
        Line frequency for notch filter (50 or 60 Hz). Set to None to disable filtering.
    annotations : dict, optional
        Dictionary of annotations with format:
        {"label": [{"start": time_in_seconds, "duration": duration_in_seconds}, ...], ...}
        Example: {"eyes_open": [{"start": 0, "duration": 15}], 
                  "eyes_closed": [{"start": 15, "duration": 15}]}
        
    Returns:
    --------
    str : Path to the created EDF file
    
    Example:
    --------
    >>> json_to_edf('data/recording.json', 'output.edf', subject_name='Subject01')
    'output.edf'
    >>> # With annotations:
    >>> annotations = {"eyes_open": [{"start": 0, "duration": 30}],
    ...                "eyes_closed": [{"start": 30, "duration": 30}]}
    >>> json_to_edf('data/recording.json', 'output.edf', annotations=annotations)
    'output.edf'
    """
    # Generate output filename if not provided
    if output_filename is None:
        json_path = Path(json_filename)
        output_filename = str(json_path.with_suffix('.edf'))
    
    # Load the EEG data
    metadata, eeg_df, motion_df, ppg_df = load_eeg(json_filename, line_freq=line_freq)
    
    # Extract patient name from metadata if not provided
    if subject_name is None:
        subject_name = metadata.get('username', 'Unknown')
        if subject_name == '#{user.username}':  # Handle template placeholder
            subject_name = 'Unknown'
    
    # Export to EDF
    return export_to_edf(
        output_filename=output_filename,
        metadata=metadata,
        eeg_df=eeg_df,
        motion_df=motion_df,
        ppg_df=ppg_df,
        subject_name=subject_name,
        include_motion=include_motion,
        include_ppg=include_ppg,
        annotations=annotations
    )


def calc_bands_power(x, dt, bands):
    f, psd = signal.welch(x, fs=1. / dt)
    power = {band: np.abs(np.mean(psd[np.where((f >= lf) & (f <= hf))])) 
                          for band, (lf, hf) in bands.items()}
    return power


def lzc(x):
    """
    Compute the Lempel-Ziv Complexity on a timeseries x of real numbers.
    This is computed by taking the analytical signal of x (using 
    scipy.signal.hilbert) and creating a series of bits by thresholding
    with meadian of the amplitude.
    """
    h = hilbert(x)
    amp = np.abs(h)
    bitstr = ''.join([str(b) for b in (amp > np.median(amp)).astype(int)])
    complexity = antropy.lziv_complexity(bitstr)
    ph = np.angle(h)
    bitstr = ''.join([str(b) for b in (ph > np.median(ph)).astype(int)])
    ph_complexity = antropy.lziv_complexity(bitstr)
    return complexity, ph_complexity


def logistic(a=4, n=100000, x0=0.4):
    x = np.zeros(n)
    x[0] = x0
    for i in range(n-1):
        x[i+1] = a*x[i]*(1-x[i])
    return(x)


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    #y = signal.lfilter(b, a, data)
    y = signal.filtfilt(b, a, data)
    return y
    

def compute_average_power_spectrum(eeg_data, sample_rate=256, window_duration=1.0, drop_first_n=0, drop_last_m=0):
    """
    Compute the average power spectrum of EEG data by dividing it into chunks and averaging their spectra.
    
    Parameters:
    -----------
    eeg_data : numpy.ndarray
        Input EEG time series data
    sample_rate : float, optional
        Sampling rate of the EEG data in Hz (default: 256)
    window_duration : float, optional
        Duration of each chunk in seconds (default: 1.0)
    drop_first_n : int, optional
        Number of chunks to drop from the beginning (default: 0)
    drop_last_m : int, optional
        Number of chunks to drop from the end (default: 0)
    
    Returns:
    --------
    frequencies : numpy.ndarray
        Array of frequency values corresponding to the power spectrum
    average_spectrum : numpy.ndarray
        Average power spectrum across all chunks
    """
    # Calculate number of samples per window
    samples_per_window = int(window_duration * sample_rate)
    
    # Calculate number of complete windows
    n_windows = len(eeg_data) // samples_per_window
    
    # Validate drop parameters
    if drop_first_n + drop_last_m >= n_windows:
        raise ValueError("The sum of drop_first_n and drop_last_m must be less than the total number of windows")
    
    # Initialize array to store all spectra
    all_spectra = []
    
    # Process each window, excluding the specified chunks
    for i in range(drop_first_n, n_windows - drop_last_m):
        start_idx = i * samples_per_window
        end_idx = start_idx + samples_per_window
        
        # Extract window of data
        window_data = eeg_data[start_idx:end_idx]
        
        # Compute power spectrum using Welch's method
        frequencies, spectrum = signal.welch(window_data, 
                                           fs=sample_rate,
                                           nperseg=samples_per_window,
                                           noverlap=samples_per_window//2)
        
        all_spectra.append(spectrum)
    
    # Convert to numpy array and compute average
    all_spectra = np.array(all_spectra)
    average_spectrum = np.mean(all_spectra, axis=0)
    
    return frequencies, average_spectrum 


def inspect_resting_eeg(edf_path, eeg_channels=None, time_window=(0, 30), sfreq=256):
    """
    Generate inspection plots for resting-state EEG data.
    
    Parameters
    ----------
    edf_path : str
        Path to the EDF file
    eeg_channels : list, optional
        List of EEG channel names to analyze. If None, auto-detects.
    time_window : tuple
        (start, end) time in seconds for detailed view
    sfreq : float
        Sampling frequency (used for calculations)
    """
    
    # Load data
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
    sfreq = raw.info['sfreq']
    
    # Auto-detect EEG channels if not specified
    if eeg_channels is None:
        # Common EEG channel patterns (exclude motion/ppg)
        eeg_channels = [ch for ch in raw.ch_names 
                       if not any(x in ch.lower() for x in ['acc', 'gyr', 'ppg', 'ecg', 'eog'])]
    
    # Pick only EEG channels for analysis
    raw_eeg = raw.copy().pick(eeg_channels)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(4, 2, figure=fig, height_ratios=[1.5, 1, 1.2, 1])
    
    # =========================================================================
    # 1. RAW TIMESERIES (full recording overview)
    # =========================================================================
    ax1 = fig.add_subplot(gs[0, :])
    data, times = raw_eeg[:, :]
    data_uv = data * 1e6  # Convert to microvolts
    
    # Plot each channel with offset
    offsets = np.arange(len(eeg_channels)) * 100  # 100 uV spacing
    for i, ch in enumerate(eeg_channels):
        ax1.plot(times, data_uv[i] + offsets[i], linewidth=0.5, label=ch)
    
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude (μV) + offset')
    ax1.set_title(f'Raw EEG Timeseries - Full Recording ({times[-1]:.1f}s)')
    ax1.set_yticks(offsets)
    ax1.set_yticklabels(eeg_channels)
    ax1.set_xlim(times[0], times[-1])
    ax1.grid(True, alpha=0.3)
    
    # =========================================================================
    # 2. ZOOMED TIMESERIES (detailed view)
    # =========================================================================
    ax2 = fig.add_subplot(gs[1, 0])
    start_samp = int(time_window[0] * sfreq)
    end_samp = int(time_window[1] * sfreq)
    
    for i, ch in enumerate(eeg_channels):
        ax2.plot(times[start_samp:end_samp], 
                data_uv[i, start_samp:end_samp] + offsets[i], 
                linewidth=0.8, label=ch)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Amplitude (μV) + offset')
    ax2.set_title(f'Zoomed View: {time_window[0]}-{time_window[1]}s')
    ax2.set_yticks(offsets)
    ax2.set_yticklabels(eeg_channels)
    ax2.grid(True, alpha=0.3)
    
    # =========================================================================
    # 3. POWER SPECTRAL DENSITY
    # =========================================================================
    ax3 = fig.add_subplot(gs[1, 1])
    
    for i, ch in enumerate(eeg_channels):
        freqs, psd = signal.welch(data[i], fs=sfreq, nperseg=int(2*sfreq))
        ax3.semilogy(freqs, psd * 1e12, label=ch, alpha=0.8)  # Convert to μV²/Hz
    
    # Mark frequency bands
    bands = {'δ': (0.5, 4), 'θ': (4, 8), 'α': (8, 13), 'β': (13, 30), 'γ': (30, 50)}
    colors = ['#FFE4E1', '#E6E6FA', '#90EE90', '#FFFACD', '#FFE4B5']
    for (band, (f_low, f_high)), color in zip(bands.items(), colors):
        ax3.axvspan(f_low, f_high, alpha=0.3, color=color, label=f'{band} ({f_low}-{f_high}Hz)')
    
    ax3.set_xlabel('Frequency (Hz)')
    ax3.set_ylabel('Power (μV²/Hz)')
    ax3.set_title('Power Spectral Density')
    ax3.set_xlim(0.5, 50)
    ax3.legend(loc='upper right', fontsize=8, ncol=2)
    ax3.grid(True, alpha=0.3)
    
    # =========================================================================
    # 4. SPECTROGRAM (time-frequency representation)
    # =========================================================================
    ax4 = fig.add_subplot(gs[2, :])
    
    # Use first EEG channel for spectrogram
    ch_idx = 0
    f, t, Sxx = signal.spectrogram(data[ch_idx], fs=sfreq, 
                                    nperseg=int(2*sfreq), 
                                    noverlap=int(1.5*sfreq),
                                    nfft=int(4*sfreq))
    
    # Limit frequency range
    freq_mask = f <= 50
    im = ax4.pcolormesh(t, f[freq_mask], 10*np.log10(Sxx[freq_mask] * 1e12 + 1e-10), 
                        shading='gouraud', cmap='viridis')
    plt.colorbar(im, ax=ax4, label='Power (dB μV²/Hz)')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Frequency (Hz)')
    ax4.set_title(f'Spectrogram - Channel {eeg_channels[ch_idx]}')
    
    # Mark alpha band
    ax4.axhline(y=8, color='white', linestyle='--', alpha=0.5)
    ax4.axhline(y=13, color='white', linestyle='--', alpha=0.5)
    
    # =========================================================================
    # 5. ARTIFACT DETECTION
    # =========================================================================
    ax5 = fig.add_subplot(gs[3, 0])
    
    # Compute artifact metrics per epoch (1-second windows)
    epoch_duration = 1.0  # seconds
    n_samples_epoch = int(epoch_duration * sfreq)
    n_epochs = len(times) // n_samples_epoch
    
    # Metrics: peak-to-peak amplitude, variance, high-frequency power
    ptp_values = np.zeros((len(eeg_channels), n_epochs))
    hf_power = np.zeros((len(eeg_channels), n_epochs))
    
    for i, ch in enumerate(eeg_channels):
        for epoch in range(n_epochs):
            start = epoch * n_samples_epoch
            end = start + n_samples_epoch
            segment = data_uv[i, start:end]
            
            # Peak-to-peak amplitude
            ptp_values[i, epoch] = np.ptp(segment)
            
            # High-frequency power (muscle artifact indicator, 30-50 Hz)
            freqs_seg, psd_seg = signal.welch(segment, fs=sfreq, nperseg=n_samples_epoch//2)
            hf_mask = (freqs_seg >= 30) & (freqs_seg <= 50)
            hf_power[i, epoch] = np.mean(psd_seg[hf_mask])
    
    # Plot peak-to-peak amplitude over time
    epoch_times = np.arange(n_epochs) * epoch_duration
    for i, ch in enumerate(eeg_channels):
        ax5.plot(epoch_times, ptp_values[i], label=ch, alpha=0.8)
    
    # Mark potential artifacts (>200 μV peak-to-peak is often considered an artifact)
    artifact_threshold = 200
    ax5.axhline(y=artifact_threshold, color='red', linestyle='--', 
                label=f'Artifact threshold ({artifact_threshold} μV)')
    
    ax5.set_xlabel('Time (s)')
    ax5.set_ylabel('Peak-to-Peak Amplitude (μV)')
    ax5.set_title('Artifact Detection: Peak-to-Peak Amplitude per 1s Epoch')
    ax5.legend(loc='upper right', fontsize=8)
    ax5.grid(True, alpha=0.3)
    
    # =========================================================================
    # 6. ARTIFACT SUMMARY & CHANNEL QUALITY
    # =========================================================================
    ax6 = fig.add_subplot(gs[3, 1])
    
    # Calculate quality metrics for each channel
    mean_ptp = np.mean(ptp_values, axis=1)
    std_ptp = np.std(ptp_values, axis=1)
    artifact_epochs = np.sum(ptp_values > artifact_threshold, axis=1)
    artifact_pct = 100 * artifact_epochs / n_epochs
    
    # Bar plot of artifact percentage per channel
    x_pos = np.arange(len(eeg_channels))
    colors = ['green' if pct < 10 else 'orange' if pct < 30 else 'red' for pct in artifact_pct]
    bars = ax6.bar(x_pos, artifact_pct, color=colors, alpha=0.7)
    
    ax6.set_xlabel('Channel')
    ax6.set_ylabel('Epochs with Artifacts (%)')
    ax6.set_title('Channel Quality Summary')
    ax6.set_xticks(x_pos)
    ax6.set_xticklabels(eeg_channels, rotation=45)
    ax6.axhline(y=10, color='green', linestyle='--', alpha=0.5, label='Good (<10%)')
    ax6.axhline(y=30, color='orange', linestyle='--', alpha=0.5, label='Moderate (<30%)')
    ax6.legend(loc='upper right', fontsize=8)
    ax6.grid(True, alpha=0.3)
    
    # Add text annotations
    for i, (bar, pct) in enumerate(zip(bars, artifact_pct)):
        ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("RESTING-STATE EEG INSPECTION SUMMARY")
    print("="*60)
    print(f"File: {edf_path}")
    print(f"Duration: {times[-1]:.1f} seconds")
    print(f"Sampling rate: {sfreq} Hz")
    print(f"Channels: {eeg_channels}")
    print(f"\nArtifact Detection (threshold: {artifact_threshold} μV peak-to-peak):")
    for i, ch in enumerate(eeg_channels):
        quality = "GOOD" if artifact_pct[i] < 10 else "MODERATE" if artifact_pct[i] < 30 else "POOR"
        print(f"  {ch}: {artifact_pct[i]:.1f}% bad epochs, mean PtP={mean_ptp[i]:.1f}μV [{quality}]")
    
    return fig, raw
