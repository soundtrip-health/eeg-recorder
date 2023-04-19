# Analysis Imports
import math
import numpy as np
from scipy.signal.windows import dpss
from scipy.signal import detrend
# Logistical Imports
import warnings
import timeit
from functools import partial
from multiprocessing import Pool, cpu_count


# MULTITAPER SPECTROGRAM #
def multitaper_spectrogram(data, fs, freq_range=None, time_bandwidth=5, num_tapers=None, window_params=None,
                           min_nfft=0, detrend_opt='linear', ncores=1):
    """ 
    Compute multitaper spectrogram of timeseries data

    Results tend to agree with Prerau Lab Matlab implementation of multitaper spectrogram with precision on the order
    of at most 10^-12 with SD of at most 10^-10
       :param data: (1d np.array) time series data -- required
       :param fs: (float) sampling frequency in Hz  -- required
       :param freq_range: (list) 1x2 list - [<min frequency>, <max frequency>] (default: [0 nyquist])
       :param time_bandwidth: (float) time-half bandwidth product (window duration*half bandwidth of main lobe)
                              (default: 5 Hz*s)
       :param num_tapers: (int) number of DPSS tapers to use (default: [will be computed
                          as floor(2*time_bandwidth - 1)])
       :param window_params: (list) 1x2 list - [window size (seconds), step size (seconds)] (default: [5 1])
       :param detrend_opt: (string) detrend data window ('linear' (default), 'constant', 'off')
       :param min_nfft: (int) minimum allowable NFFT size, adds zero padding for interpolation (closest 2^x) (default: 0)
       :param ncores: (int) Number of cores to use (set to -1 to use all cores; default: 1, no multiprocess). 
        
        :return mt_spectrogram: (TxF np array): spectral power matrix
        :return stimes: (1xT np array): timepoints (s) in mt_spectrogram
        :return sfreqs: (1xF np array)L frequency values (Hz) in mt_spectrogram
        :return meta: dict of some useful metadata
    """

    #  Process user input
    if len(data.shape) != 1:
        raise TypeError('Input should be a 1d array with shape (n,) where n is the number of data points.')

    if not freq_range:
        freq_range = [0, fs / 2]

    if detrend_opt not in ['linear', 'constant', 'off']:
        raise ValueError('detrend_opt must be one of "constant", "linear", or "off".')

    if freq_range[1] > fs / 2:
        freq_range[1] = fs / 2
        warnings.warn(f'Upper frequency greater than Nyquist; setting to [{freq_range[0]}, {freq_range[1]}]')

    if not num_tapers:
        num_tapers = math.floor(2 * time_bandwidth) - 1
    elif num_tapers != math.floor(2 * time_bandwidth) - 1:
        warnings.warn(f'Optimal num_tapers is floor(2*TW) - 1 ({math.floor(2 * time_bandwidth) - 1})')

    if not window_params:
        # window_params = [5, 1]
        winsize_samples = 5 * fs
        winstep_samples = fs
    else:
        # winsize/winstep must be an integer (can fail if window_params are not integers)
        winsize_samples = round(window_params[0] * fs)
        winstep_samples = round(window_params[1] * fs)
        if window_params[0] * fs % 1 != 0:
            warnings.warn(f'Window size not divisible by sampling frequency; adjusting to {winsize_samples / fs}.')
        if window_params[1] * fs % 1 != 0:
            warnings.warn(f'Window step not divisible by sampling frequency; adjusting to {winstep_samples / fs}.')

    len_data = len(data)
    if len_data < winsize_samples:
        raise ValueError(f'\nData length ({len_data} is < window size {winsize_samples}!')

    window_start = np.arange(0, len_data - winsize_samples + 1, winstep_samples)
    num_windows = len(window_start)

    if min_nfft == 0:  # avoid divide by zero error in np.log2(0)
        nfft = max(2 ** math.ceil(np.log2(abs(winsize_samples))), winsize_samples)
    else:
        nfft = max(max(2 ** math.ceil(np.log2(abs(winsize_samples))), winsize_samples),
                   2 ** math.ceil(np.log2(abs(min_nfft))))

    # Create frequency vector and window indices for spectrogram
    sfreqs = np.arange(fs / nfft / 2, fs, fs / nfft)
    freq_inds = (sfreqs >= freq_range[0]) & (sfreqs <= freq_range[1])
    sfreqs = sfreqs[freq_inds]

    # Compute times in the middle of each spectrum
    window_middle_times = window_start + round(winsize_samples / 2)
    stimes = window_middle_times / fs

    # Get indexes for each window
    window_idxs = np.atleast_2d(window_start).T + np.arange(0, winsize_samples, 1)
    window_idxs = window_idxs.astype(int)

    # Split data into segments and preallocate
    data_segments = data[window_idxs]

    # COMPUTE THE MULTITAPER SPECTROGRAM
    #     STEP 1: Compute DPSS tapers based on desired spectral properties
    #     STEP 2: Multiply the data segment by the DPSS Tapers
    #     STEP 3: Compute the spectrum for each tapered segment
    #     STEP 4: Take the mean of the tapered spectra

    # Compute DPSS tapers (STEP 1)
    DPSS_tapers = dpss(winsize_samples, time_bandwidth, num_tapers) * math.sqrt(fs)

    tic = timeit.default_timer()  # start timer

    # set all but 1 arg of calc_mts_segment to constant (so we only have to supply one argument later)
    calc_mts_segment_plus_args = partial(calc_mts_segment, DPSS_tapers=DPSS_tapers, nfft=nfft,
                                         freq_inds=freq_inds, detrend_opt=detrend_opt)

    if ncores != 1: # use multiprocessing
        if ncores == -1:
            pool = Pool(cpu_count()-1)
        else:
            pool = Pool(ncores)
        mt_spectrogram = pool.map(calc_mts_segment_plus_args, data_segments)
        pool.close()
        pool.join()
    else: # if no multiprocessing, compute normally
        mt_spectrogram = np.apply_along_axis(calc_mts_segment_plus_args, 1, data_segments)

    # Compute mean fft magnitude (STEP 4.2)
    mt_spectrogram = np.asarray(mt_spectrogram)
    mt_spectrogram = mt_spectrogram.conj().T / fs ** 2 / num_tapers

    # End timer and get elapsed compute time
    toc = timeit.default_timer()
    meta = {'Spectral resolution (Hz)': 2 * time_bandwidth / winsize_samples,
            'Window length (s)': winsize_samples / fs,
            'Window step (s)': winstep_samples / fs,
            'Time half-bandwidth product': time_bandwidth,
            'Number of tapers': num_tapers,
            'Minimum frequency (Hz)': freq_range[0], 
            'Maximum frequency (Hz)': freq_range[1],
            'Detrend': detrend_opt,
            'Compute time (s)': toc - tic}

    # Put outputs into better format for output
    #mt_spectrogram = mt_spectrogram.T
    #stimes = np.mat(stimes)
    #sfreqs = np.mat(sfreqs)

    return mt_spectrogram, stimes, sfreqs, meta


    return ([data, fs, freq_range, time_bandwidth, num_tapers,
             winsize_samples, winstep_samples, window_start, num_windows, nfft,
             detrend_opt, plot_on, verbose])


# NANPOW2DB
def nanpow2db(y):
    """ Power to dB conversion, setting bad values to nans
        Arguments:
            y (float or array-like): power
        Returns:
            ydB (float or np array): inputs converted to dB with 0s and negatives resulting in nans
    """

    if isinstance(y, int) or isinstance(y, float):
        if y == 0:
            return np.nan
        else:
            ydB = 10 * np.log10(y)
    else:
        if isinstance(y, list):  # if list, turn into array
            y = np.asarray(y)
        y = y.astype(float)  # make sure it's a float array so we can put nans in it
        y[y == 0] = np.nan
        ydB = 10 * np.log10(y)

    return ydB


# CALCULATE MULTITAPER SPECTRUM ON SINGLE SEGMENT
def calc_mts_segment(data_segment, DPSS_tapers, nfft, freq_inds, detrend_opt):
    """ Helper function to calculate the multitaper spectrum of a single segment of data
        Arguments:
            data_segment (1d np.array): One window worth of time-series data -- required
            DPSS_tapers (2d np.array): Parameters for the DPSS tapers to be used.
                                       Dimensions are (num_tapers, winsize_samples) -- required
            nfft (int): length of signal to calculate fft on -- required
            freq_inds (1d np array): boolean array of which frequencies are being analyzed in
                                      an array of frequencies from 0 to fs with steps of fs/nfft
            detrend_opt (str): detrend data window ('linear' (default), 'constant', 'off')
        Returns:
            mt_spectrum (1d np.array): spectral power for single window
    """

    # If segment has all zeros, return vector of zeros
    if all(data_segment == 0):
        ret = np.empty(sum(freq_inds))
        ret.fill(0)
        return ret

    # Option to detrend data to remove low frequency DC component
    if detrend_opt != 'off':
        data_segment = detrend(data_segment, type=detrend_opt)

    # Multiply data by dpss tapers (STEP 2)
    tapered_data = np.multiply(np.mat(data_segment).T, np.mat(DPSS_tapers.T))

    # Compute the FFT (STEP 3)
    fft_data = np.fft.fft(tapered_data, nfft, axis=0)
    fft_range = fft_data[freq_inds, :]

    # Take the FFT magnitude (STEP 4.1)
    magnitude = np.power(np.imag(fft_range), 2) + np.power(np.real(fft_range), 2)
    mt_spectrum = np.sum(magnitude, axis=1)

    return mt_spectrum
