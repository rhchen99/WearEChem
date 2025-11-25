import oktop_driver as oktop
import oktop_config as cfg


if __name__ == "__main__":

    # ---------------------------------------------------------------
    # system initialization
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
    fpga.set_modes(task_mode=0, dac_mode=0, adc_mode=0)

    # ---------------------------------------------------------------
    # SPI configuration generation
    # I_MUX_OUT: 0 = current to ADC, 1 = current to output
    # ION_EN:    0 = iontophoresis off, 1 = iontophoresis on
    # PM_EN:     0 = process monitor off, 1 = process monitor on
    # ---------------------------------------------------------------
    msb, lsb = fpga.gen_config_code(I_MUX_OUT=0, ION_EN=0, PM_EN=0, ADC_MUX=0)

    # ---------------------------------------------------------------
    # Waveform generation options:
    # gen_ramp: genrerate a ramp waveform
    # gen_cv: generate a cyclic voltammetry waveform
    # gen_dpv: generate a differential pulse voltammetry waveform
    # ---------------------------------------------------------------
    print("Generating waveform...")
    wav = fpga.gen_ramp(vstart=2400, vstop=2560, vstep=10)
    print(f"Generated waveform with {len(wav)} samples.")
    
    # ---------------------------------------------------------------
    # DAC options:
    # t1: cycles in period 1
    # t2: cycles in period 2
    # ts1: settling time before kicking adc in period 1
    # ts2: settling time before kicking adc in period 2
    # ---------------------------------------------------------------
    fpga.config_dac(t1=100, t2=200, ts1=50, ts2=50, nsam=len(wav))

    # ---------------------------------------------------------------
    # ADC options:
    # twake: cycles for adc wake up
    # tsample: in free-running mode, this is the number of samples
    #          in incremental mode, this is the number of samples for average
    # nsam:    not used in free-running mode
    #          in incremental mode, this is the number of decimated samples
    # ---------------------------------------------------------------
    fpga.config_adc(twake=100, tsample=2**20, nsam=1)

    # ---------------------------------------------------------------
    # load configuration and waveform into FIFOs
    # ---------------------------------------------------------------
    fpga.write_spi_config_word40(msb_32=msb, lsb_32=lsb)
    fpga.write_waveform_words(wav)

    # ---------------------------------------------------------------
    # trigger SPI (should trigger 4 times)
    # ---------------------------------------------------------------
    fpga.trigger_spi_config()
    fpga.read_spi_cnt()
    
    # ---------------------------------------------------------------
    # trigger task FSM and wait for completion   
    # ---------------------------------------------------------------
    fpga.trigger_task()
    data = fpga.task_watcher()

    # ---------------------------------------------------------------
    # optional: read SPI output
    # ---------------------------------------------------------------
    #spi_data_msb = fpga.read_spi_out_msb(4)
    #spi_data_lsb = fpga.read_spi_out_lsb(4)
    #print("SPI out (MSB) words:", [hex(x) for x in spi_data_msb])
    #print("SPI out (LSB) words:", [hex(x) for x in spi_data_lsb])

    # ---------------------------------------------------------------
    # data processing
    # ---------------------------------------------------------------
    with open("output.csv", "w") as f:
        for item in data:
            f.write(f"{item}\n")
