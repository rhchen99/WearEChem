import oktop_driver as oktop
import oktop_config as cfg
import ds360_driver as ds360
import cs580_driver as cs580
import time

if __name__ == "__main__":

    # ---------------------------------------------------------------
    # DS360 initialization
    # ---------------------------------------------------------------
    vsrc = ds360.DS360()
    vsrc.set_sine_waveform()
    vsrc.set_offset(0)
    vsrc.set_frequency(499.633)      
    vsrc.set_amplitude(0.7071)
    vsrc.output_on()
    # ---------------------------------------------------------------
    # CS580 initialization
    # ---------------------------------------------------------------
    isrc = cs580.CS580('COM3')
    isrc.enable_output(0)
    isrc.set_gain(100e-9)
    isrc.set_speed('FAST')
    isrc.set_shield('GUARD')
    isrc.set_isolation('GROUND')
    isrc.set_compliance_voltage(3)
    isrc.enable_analog_input(1)
    isrc.enable_output(1)

    # ---------------------------------------------------------------
    # FPGA initialization
    # ---------------------------------------------------------------
    bitfile = cfg.BITFILE
    fpga = oktop.OKTop(bitfile)
    fpga.open_and_configure()
    
    fpga.set_ldo_en_all(vrefdac=1, wegd=1, avdd3v0=1, vcm=1, ion3v0=1, ion1v8=1, dvdd1v8=1, avdd1v8=1)
    fpga.system_reset()
    fpga.set_force_awake(0)
    # ---------------------------------------------------------------
    # Waveform generation options:
    # gen_ramp: genrerate a ramp waveform
    # gen_cv: generate a cyclic voltammetry waveform
    # gen_dpv: generate a differential pulse voltammetry waveform
    # ---------------------------------------------------------------
    wav = fpga.gen_ramp(vstart=0, vstop=2560, vstep=10)
    fpga.write_waveform_words(wav) # load waveform into FIFO

    # ---------------------------------------------------------------
    # Set operating modes
    # task_mode: 0 = ADC only, 1 = DAC
    # dac_mode:  0 = DAC only, 1 = ADC Enabled
    # adc_mode:  0 = Free-running, 1 = Incremental
    # ---------------------------------------------------------------
    fpga.set_modes(task_mode=0, dac_mode=0, adc_mode=1)
    
    # ---------------------------------------------------------------
    # DAC options:
    # t1: cycles in period 1
    # t2: cycles in period 2
    # ts1: settling time before kicking adc in period 1
    # ts2: settling time before kicking adc in period 2
    # ---------------------------------------------------------------
    fpga.config_dac(t1=51200, t2=51200, ts1=500, ts2=500, nsam=len(wav))

    # ---------------------------------------------------------------
    # ADC options:
    # twake: cycles for adc wake up
    # tsample: in free-running mode, this is the number of samples
    #          in incremental mode, this is the number of samples for average
    # nsam:    not used in free-running mode
    #          in incremental mode, this is the number of decimated samples
    # ---------------------------------------------------------------
    fpga.config_adc(twake=100, tsample=256, nsam=2**18)

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
    fpga.set_cc_gain(10)  # 0.1x, 1x, 10x
    fpga.set_cc_sel(10)   # 1 ... 11
    fpga.set_pstat_sleep(bias=0, cc=0, otaw=0, clsabw=0, otar=0, clsabr=0, sre=0)
    fpga.set_pstat_i2x_all(otaw=0, otar=0, clsabw=0, clsabr=0)
    # ---------------------------------------------------------------
    # SPI ADC configuration
    # ---------------------------------------------------------------
    fpga.set_adc_mux(2)
    fpga.set_adc_ota1(1)
    fpga.set_adc_ota2(1)
    fpga.set_adc_startup_sel(2)
    fpga.set_adc_c2(2)
    # ---------------------------------------------------------------
    # config through SPI, should be called before triggering task
    # ---------------------------------------------------------------
    fpga.config_through_spi()
    time.sleep(1)  # wait for configuration to settle
    # ---------------------------------------------------------------
    # trigger task FSM and wait for completion   
    # ---------------------------------------------------------------
    fpga.trigger_task()
    data = fpga.task_watcher()
    
    # ---------------------------------------------------------------
    # optional: read SPI output
    # ---------------------------------------------------------------
    # spi_data_msb = fpga.read_spi_out_msb(4)
    # spi_data_lsb = fpga.read_spi_out_lsb(4)
    # print("SPI out (MSB) words:", [hex(x) for x in spi_data_msb])
    # print("SPI out (LSB) words:", [hex(x) for x in spi_data_lsb])

    # ---------------------------------------------------------------
    # shutdown ds360 and close connections
    # ---------------------------------------------------------------
    vsrc.output_off()
    vsrc.close()

    isrc.enable_output(0)
    isrc.close()

    # ---------------------------------------------------------------
    # data processing
    # ---------------------------------------------------------------
    with open("output.csv", "w") as f:
        for item in data:
            f.write(f"{item}\n")
