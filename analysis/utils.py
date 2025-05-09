from pathlib import Path
import pandas as pd
import numpy as np
import json
from scipy import signal
from scipy.signal import hilbert 
#from lempel_ziv_complexity import lempel_ziv_complexity
import ordpy
import antropy

EEG_FS = 256
MOT_FS = 52
PPG_FS = 64
EEG_DT = 1 / EEG_FS
MOT_DT = 1 / MOT_FS
PPG_DT = 1 / PPG_FS

def load_eeg(json_filename, line_freq=60):
    with open(json_filename) as fp:
        jsn = json.load(fp)
    #print(f'start: {jsn["start_ts"]}, end: {jsn["end_ts"]}, metadata: {jsn["metadata"]}')
    
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