import numpy as np
from sympy import primerange, nextprime

import csv
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Coherent sampling
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Configuration dataclasses
# -----------------------------------------------------------------------------


@dataclass
class TestingSetup:
    chip_id: int = 0
    motherboard_id: int = 0


@dataclass
class ADCSamplingConfig:
    fs: float = 0
    fin_set: float = 0
    bw: float = 0
    osr: int = 0
    adc_mode_set: int = 0      # 0: free running, 1: incremental
    twake_set: int = 0
    nsam_set: int = 0          # only valid in incremental mode
    tsample_set: int = 0       # total sampling points
    input_current_pk: float = 0
    ds360_output_voltage_rms: float = 0
    cs580_gain:int = 0


@dataclass
class ADCTrimBitsConfig:
    adc_mux_set: int = 0
    adc_ota1_set: int = 0
    adc_ota2_set: int = 0
    adc_startup_sel_set: int = 0
    adc_c2_set: int = 0

# -----------------------------------------------------------------------------
# CSV logging
# -----------------------------------------------------------------------------

def save_to_csv(testing_setup: TestingSetup,
                adc_sampling: ADCSamplingConfig,
                adc_trim: ADCTrimBitsConfig,
                data_list):
    """
    Save config blocks and data_list to a CSV.

    CSV name: ADC_Testing_<timestamp>.csv
    Location: Chip_<chip_id>/Test_Data
    """

    # Folder: Chip_<chip_id>/Test_Data
    folder = Path("Test_Data") / f"Chip_{testing_setup.chip_id}"
    folder.mkdir(parents=True, exist_ok=True)

    # File name: ADC_Testing_<current time>.csv
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = folder / f"ADC_Measurement_{timestamp}.csv"

    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)

        # ---- Testing Setup ----
        writer.writerow(["Testing Setup"])
        writer.writerow(["chip_id", testing_setup.chip_id])
        writer.writerow(["motherboard_id", testing_setup.motherboard_id])
        writer.writerow([])

        # ---- ADC Sampling Config ----
        writer.writerow(["ADC Sampling Config"])
        writer.writerow(["fs", adc_sampling.fs])
        writer.writerow(["bw", adc_sampling.bw])
        writer.writerow(["fin_set", adc_sampling.fin_set])
        writer.writerow(["osr", adc_sampling.osr])
        writer.writerow(["adc_mode_set", adc_sampling.adc_mode_set])
        writer.writerow(["twake_set", adc_sampling.twake_set])
        writer.writerow(["nsam_set", adc_sampling.nsam_set])
        writer.writerow(["tsample_set", adc_sampling.tsample_set])
        writer.writerow(["input_current_pk", adc_sampling.input_current_pk])
        writer.writerow(["ds360_output_voltage_rms", adc_sampling.ds360_output_voltage_rms])
        writer.writerow(["cs580_gain", adc_sampling.cs580_gain])
        writer.writerow([])

        # ---- ADC Trim Bits Config ----
        writer.writerow(["ADC Trim Bits Config"])
        writer.writerow(["adc_mux_set", adc_trim.adc_mux_set])
        writer.writerow(["adc_ota1_set", adc_trim.adc_ota1_set])
        writer.writerow(["adc_ota2_set", adc_trim.adc_ota2_set])
        writer.writerow(["adc_startup_sel_set", adc_trim.adc_startup_sel_set])
        writer.writerow(["adc_c2_set", adc_trim.adc_c2_set])

        # ---- Empty row between variables and list ----
        writer.writerow([])

        # ---- Data list section ----
        writer.writerow(["ADC Output Data"])
        for row in data_list:
            if isinstance(row, (list, tuple)):
                writer.writerow(row)
            else:
                writer.writerow([row])

    print(f"Saved CSV to: {csv_path}")
