import oktop_driver as oktop
import oktop_config as cfg
import ds360_driver as ds360

import math

from adc_test_func import (
    TestingSetup,
    ADCSamplingConfig,
    ADCTrimBitsConfig,
    save_to_csv,
    find_coherent_fin
)

# ---------------------------------------------------------------
# Testing parameters
# ---------------------------------------------------------------

testing_setup = TestingSetup()          # all zeros for now
adc_sampling  = ADCSamplingConfig()     # all zeros for now
adc_trim      = ADCTrimBitsConfig()     # all zeros for now

# Testing setup

testing_setup.chip_id = 2
testing_setup.motherboard_id = 2

# ADC sampling config

adc_sampling.fs = 512e3
adc_sampling.osr = 256
adc_sampling.bw = adc_sampling.fs/(2*adc_sampling.osr)
adc_sampling.fin_set = 0.125*adc_sampling.bw
adc_sampling.input_current_pk = 1e-6
adc_sampling.cs580_gain = 1e-6          # CS580 gain A/V

adc_sampling.adc_mode_set = 0           # Set to 0 for free running mode, 1 for incremental mode
adc_sampling.twake_set = 100
adc_sampling.nsam_set = 1               # Only valid in incremental mode, set to desire sampling points in incremental mode
adc_sampling.tsample_set = 2**18        # Set to desire total sampling points in free running mode, set to osr in free running mode

# ADC trim bits config

adc_trim.adc_mux_set = 0
adc_trim.adc_ota1_set = 1
adc_trim.adc_ota2_set = 1
adc_trim.adc_startup_sel_set = 3
adc_trim.adc_c2_set = 2


if __name__ == "__main__":

    # ---------------------------------------------------------------
    # Find coherent sampling frequency
    # ---------------------------------------------------------------

    if adc_sampling.adc_mode_set == 0:
        Mpoints_set = adc_sampling.tsample_set
    else:
        Mpoints_set = adc_sampling.nsam_set
    
    N, fin, info = find_coherent_fin(fs=adc_sampling.fs, Mpoints=Mpoints_set, fin_set=adc_sampling.fin_set)
    print(f"Coherent cycles N   : {N}")
    print(f"Actual coherent fin : {fin:.3f} Hz")
    print(f"Min |fin error|     : {info['fh_error_temp']:.3f} Hz")

    # ---------------------------------------------------------------
    # DS360 initialization
    # ---------------------------------------------------------------

    ds360_output_voltage_pk = adc_sampling.input_current_pk/adc_sampling.cs580_gain
    ds360_output_voltage_rms = ds360_output_voltage_pk/math.sqrt(2)
    adc_sampling.ds360_output_voltage_rms = ds360_output_voltage_rms

    # vsrc = ds360.DS360()
    # vsrc.set_sine_waveform()
    # vsrc.set_offset(0)
    # vsrc.set_frequency(fin)      
    # vsrc.set_amplitude(ds360_output_voltage_rms)
    # vsrc.output_on()
    # ---------------------------------------------------------------
    # FPGA initialization
    # ---------------------------------------------------------------
    bitfile = cfg.BITFILE
    fpga = oktop.OKTop(bitfile)
    fpga.open_and_configure()
    fpga.system_reset()

    # ---------------------------------------------------------------
    # Set operating modes
    # task_mode: 0 = ADC only, 1 = DAC
    # dac_mode:  0 = DAC only, 1 = ADC Enabled
    # adc_mode:  0 = Free-running, 1 = Incremental
    # ---------------------------------------------------------------
    fpga.set_modes(task_mode=0, dac_mode=1, adc_mode = adc_sampling.adc_mode_set)
    

    # ---------------------------------------------------------------
    # ADC options:
    # twake: cycles for adc wake up
    # tsample: in free-running mode, this is the number of samples
    #          in incremental mode, this is the number of samples for average
    # nsam:    not used in free-running mode
    #          in incremental mode, this is the number of decimated samples
    # ---------------------------------------------------------------
    fpga.config_adc(twake = adc_sampling.twake_set, tsample = adc_sampling.tsample_set, nsam = adc_sampling.nsam_set)

    # ---------------------------------------------------------------
    # SPI system configuration
    # ---------------------------------------------------------------
    fpga.set_imux_out(0) # 0 = current to ADC, 1 = current to output
    fpga.set_cgm_ext(0)  # 0 = internal CGM, 1 = external CGM
    fpga.set_ion_en(0)   # 0 = iontophoresis off, 1 = iontophoresis on
    fpga.set_pm_en(0)    # 0 = process monitor off, 1 = process monitor on
    # ---------------------------------------------------------------
    # SPI potentiostat configuration
    # ---------------------------------------------------------------
    fpga.set_cc_gain(1)  # 0.1x, 1x, 10x
    fpga.set_cc_sel(5)   # 1 ... 11
    fpga.set_pstat_sleep(bias=0, cc=0, otaw=0, clsabw=0, otar=0, clsabr=0, sre=0)
    fpga.set_pstat_i2x_all(otaw=0, otar=0, clsabw=0, clsabr=0)
    # ---------------------------------------------------------------
    # SPI ADC configuration
    # ---------------------------------------------------------------
    fpga.set_adc_mux(adc_trim.adc_mux_set)
    fpga.set_adc_ota1(adc_trim.adc_ota1_set)
    fpga.set_adc_ota2(adc_trim.adc_ota2_set)
    fpga.set_adc_startup_sel(adc_trim.adc_startup_sel_set)
    fpga.set_adc_c2(adc_trim.adc_c2_set)
    # ---------------------------------------------------------------
    # config through SPI, should be called before triggering task
    # ---------------------------------------------------------------
    fpga.config_through_spi()
    # ---------------------------------------------------------------
    # trigger task FSM and wait for completion   
    # ---------------------------------------------------------------
    fpga.trigger_task()
    data = fpga.task_watcher()

    # ---------------------------------------------------------------
    # optional: read SPI output
    # ---------------------------------------------------------------
    spi_data_msb = fpga.read_spi_out_msb(4)
    spi_data_lsb = fpga.read_spi_out_lsb(4)
    print("SPI out (MSB) words:", [hex(x) for x in spi_data_msb])
    print("SPI out (LSB) words:", [hex(x) for x in spi_data_lsb])

    # ---------------------------------------------------------------
    # shutdown ds360 and close connections
    # ---------------------------------------------------------------
    #vsrc.output_off()
    #vsrc.close()

    # ---------------------------------------------------------------
    # data processing
    # ---------------------------------------------------------------

    save_to_csv(testing_setup, adc_sampling, adc_trim, data)
