import numpy as np
from sympy import primerange, nextprime

def find_coherent_fin(fs: float, Mpoints: int, fin_set: float):
    """
    Compute a coherent sampling input frequency 'fin' close to 'fin_set'
    using the nearest prime number of bins.

    Parameters
    ----------
    fs : float
        Sampling frequency (Hz)
    Mpoints : int
        Number of points (FFT length)
    fin_set : float
        Desired input tone frequency (Hz)

    Returns
    -------
    N : int
        Selected prime number of bins (coherent cycles in record)
    fin : float
        Actual coherent input frequency (Hz)
    info : dict
        Extra info:
            - 'Nbins' : float, ideal (non-integer) bins
            - 'prime_candidates' : list[int], two nearest primes (<= and > Nbins)
            - 'fin_error' : np.ndarray, error of each candidate vs fin_set
            - 'fh_error_temp' : float, minimum absolute error
            - 'index' : int, index (0 or 1) of chosen candidate
    """
    # Equivalent to: Nbins = fin_set*Mpoints/fs;
    Nbins = fin_set * Mpoints / fs
    Nbins_int = int(Nbins)  # floor, like MATLAB's primes(Nbins)

    # Equivalent to: primeNums_List = [primes(Nbins), nextprime(Nbins)];
    prime_nums_list = list(primerange(2, Nbins_int + 1)) + [nextprime(Nbins_int)]

    # Equivalent to: primeNums_nearest = [primeNums_List(end-1), primeNums_List(end)];
    prime_nums_nearest = [prime_nums_list[-2], prime_nums_list[-1]]

    # fin_error = [fs*primeNums_nearest(1)/Mpoints - fin_set, ...]
    fin_error = np.array([
        fs * prime_nums_nearest[0] / Mpoints - fin_set,
        fs * prime_nums_nearest[1] / Mpoints - fin_set
    ])

    # [fh_error_temp, Index] = min(abs(fin_error));
    abs_errors = np.abs(fin_error)
    fh_error_temp = float(np.min(abs_errors))
    index = int(np.argmin(abs_errors))  # 0 or 1

    # N = primeNums_nearest(Index);
    N = prime_nums_nearest[index]

    # fin = fs*N/Mpoints;
    fin = fs * N / Mpoints

    info = {
        "Nbins": Nbins,
        "prime_candidates": prime_nums_nearest,
        "fin_error": fin_error,
        "fh_error_temp": fh_error_temp,
        "index": index,
    }

    return N, fin, info


