'''
This is the driver module for the WearEChem project.
Renhe Chen (rec004@ucsd.edu)
University of California San Diego
'''
import time
import weconfig
import ok

dev = ok.okCFrontPanel()

def task_trigger():
    '''
    Trigger a measurement task.
    '''
    dev.ActivateTriggerIn(weconfig.TASK_TRIG, 0)
    print("Measurement task triggered.")

def adc_config(mode,tsam,twake,nsam):
    '''
        confige ADC settings
        mode: ADC mode: 0 for free running, 1 for incremental
        tsam: ADC sample time (32 bits)
        twake: ADC wakeup time (32 bits)
        nsam: ADC number of samples (32 bits)
    '''
    #set ADC_MODE register
    dev.SetWireInValue(weconfig.ADC_MODE, mode)
    #set ADC_TSAM register
    dev.SetWireInValue(weconfig.ADC_TSAM, tsam)
    #set ADC_TWAKE register
    dev.SetWireInValue(weconfig.ADC_TWAKE, twake)
    #set ADC_NSAM register
    dev.SetWireInValue(weconfig.ADC_NSAM, nsam)
    dev.UpdateWireIns()
    print(f"ADC configuration complete.")

def dac_config(mode,t1,t2,ts1,ts2,nsam,data_list):
    '''
        configure DAC settings
        mode: 0 for normal mode, 1 for dpv mode
        t1: DAC time interval 1
        t2: DAC time interval 2
        nsam: number of samples
        data: list of DAC data
    '''
    #set DAC_MODE register
    dev.SetWireInValue(weconfig.DAC_MODE, mode)
    #set DAC_T1 register
    dev.SetWireInValue(weconfig.DAC_T1, t1)
    #set DAC_T2 register
    dev.SetWireInValue(weconfig.DAC_T2, t2)
    #set DAC_TS1 register
    dev.SetWireInValue(weconfig.DAC_TS1, ts1)
    #set DAC_TS2 register
    dev.SetWireInValue(weconfig.DAC_TS2, ts2)
    #set DAC_NSAM register
    dev.SetWireInValue(weconfig.DAC_NSAM, nsam)
    dev.UpdateWireIns()
    print(f'DAC configuration complete.')
    # Pack data into bytes
    dataout = b''.join(value.to_bytes(4, 'little') for value in data_list)
    # Load data to DAC buffer
    dev.WriteToPipeIn(weconfig.SPI_WAV, dataout)
    print(f'Waveform data has been loaded to DAC buffer.')

def gen_ramp(vstart,vstop,vstep):
    '''
        vstart: starting voltage (mV)
        vstop: final voltage (mV)
        vstep: step voltage (mV)
    '''
    data = []
    steps = int((vstop-vstart)/vstep + 1)
    for i in range(steps):
        v = vstart + i * vstep
        bin = analog_to_binary(v,weconfig.VREF)
        data.append(bin)
    return data

def gen_cv(vstart,v1,v2,vstep):
    '''
        vstart: starting voltage (mV)
        v1: CV turning point1 (mV)
        v2: CV turning point2 (mV)
        vstep: step voltage (mV)
    '''
    data = []
    steps = int((v1-vstart)/vstep)
    for i in range(steps):
        v = vstart + i * vstep
        bin = analog_to_binary(v,weconfig.VREF)
        data.append(bin)
    steps = int((v1-v2)/vstep + 1)
    for i in range(steps):
        v = v1 - i * vstep
        bin = analog_to_binary(v,weconfig.VREF)
        data.append(bin)
    return data

def gen_dpv(vstart,vstop,vstep,vpulse):
    '''
        vstart: starting voltage (mV)
        vstop: final voltage (mV)
        vstep: step voltage (mV)
        vpulse: DPV pulse height (mV)
    '''
    data = []
    steps = int((vstop-vstart)/vstep + 1)
    for i in range(steps):
        v = vstart + i * vstep
        bin = analog_to_binary(v,weconfig.VREF)
        data.append(bin)
        v = vstart + i * vstep + vpulse
        bin = analog_to_binary(v,weconfig.VREF)
        data.append(bin)
    return data

def spi_write(data_msb,data_lsb):
    '''
    Write data to SPI interface and read the response.
    '''
    datain_msb = 0
    datain_lsb = 0
    dataout_msb = data_msb.to_bytes(4, 'little')
    dataout_lsb = data_lsb.to_bytes(4, 'little')
    # load MSB
    dev.WriteToPipeIn(weconfig.SPI_CONFIG_MSB, dataout_msb)
    dev.WriteToPipeIn(weconfig.SPI_CONFIG_MSB, dataout_msb)
    # load LSB
    dev.WriteToPipeIn(weconfig.SPI_CONFIG_LSB, dataout_lsb)
    dev.WriteToPipeIn(weconfig.SPI_CONFIG_LSB, dataout_lsb)

    # Trigger SPI to send data into DUT
    dev.ActivateTriggerIn(weconfig.TRIG_CONFIG, 0)
    time.sleep(0.1)
    # Trigger SPI again to pop out data
    dev.ActivateTriggerIn(weconfig.TRIG_CONFIG, 0)
    time.sleep(0.1)

    # Read back from SPI output buffer
    datain_msb = dev.ReadFromPipeOut(weconfig.SPI_OUT_MSB, 4)
    datain_lsb = dev.ReadFromPipeOut(weconfig.SPI_OUT_LSB, 4)
    datain = int.from_bytes(datain_msb, 'little') << 32
    datain = datain + int.from_bytes(datain_lsb, 'little')
    # Print the data read from SPI
    print(f'{datain} has been written to SPI 0')

def fpga_init(bitfile):
    '''
    Initialize the FPGA device.
    '''
    dev.OpenBySerial("")
    dev.ResetFPGA()
    error = dev.ConfigureFPGA(bitfile)
    if error == 0:
        print("FPGA initialization complete.")
    else:
        print(f"FPGA initialization failed with error code: {error}")
    enable = dev.IsFrontPanelEnabled()
    if enable:
        print("FrontPanel is enabled.")
    else:
        print("FrontPanel is not enabled.")

def system_reset():
    '''
    Reset the system to its default state.
    '''
    #set RESET_ALL to 1
    dev.SetWireInValue(weconfig.RST_ALL, 1)
    dev.UpdateWireIns()
    #set RESET_ALL to 0
    dev.SetWireInValue(weconfig.RST_ALL, 0)
    dev.UpdateWireIns()
    print("System reset complete.")

def system_config(mode):
    '''
    Configure the system based on the selected mode.
    mode: see 'mode definition' in 'weconfig.py'
    '''
    I_MUX_OUT = 0
    ION_EN = 0
    PM_EN = 0
    ADC_MUX = 0
    if mode == weconfig.MODE_PM:
        PM_EN = 1
    elif mode == weconfig.MODE_PSTAT:
        ADC_MUX = 2
    elif mode == weconfig.MODE_ADC:
        I_MUX_OUT = 1
        ADC_MUX = 3
    elif mode == weconfig.MODE_ION:
        ION_EN = 1
        ADC_MUX = 1
    #generate 40-bit config data
    [data_msb,data_lsb] = gen_config_code(I_MUX_OUT, ION_EN, PM_EN, ADC_MUX)
    #send data to SPI
    spi_write(data_msb, data_lsb)

def gen_config_code(I_MUX_OUT,ION_EN,PM_EN,ADC_MUX):
    '''
        assemble 40-bit config code to be sent to SPI0
        with settings from weconfig.py
    '''
    lsb = binary_to_one_hot(weconfig.CC_SEL,11)
    lsb = lsb + (weconfig.CC_GAIN << 11)
    lsb = lsb + (weconfig.PSTAT_CLSABRI2X << 13)
    lsb = lsb + (weconfig.PSTAT_CLSABWI2X << 14)
    lsb = lsb + (weconfig.PSTAT_OTARI2X << 15)
    lsb = lsb + (weconfig.PSTAT_OTAWI2X << 16)
    lsb = lsb + (weconfig.PSTAT_S_SRE << 17)
    lsb = lsb + (weconfig.PSTAT_S_CLSABR << 18)
    lsb = lsb + (weconfig.PSTAT_S_OTAR << 19)
    lsb = lsb + (weconfig.PSTAT_S_CLSABW << 20)
    lsb = lsb + (weconfig.PSTAT_S_OTAW << 21)
    lsb = lsb + (weconfig.PSTAT_S_CC << 22)
    lsb = lsb + (weconfig.PSTAT_S_BIAS << 23)
    lsb = lsb + (ADC_MUX << 24)
    lsb = lsb + (binary_to_thermo(weconfig.ADC_C2) << 26)
    lsb = lsb + (weconfig.ADC_STARTUP_SEL << 30)

    msb = binary_to_thermo(weconfig.ADC_OTA2)
    msb = msb + (binary_to_thermo(weconfig.ADC_OTA1) << 2)
    msb = msb + (PM_EN << 4)
    msb = msb + (ION_EN << 5)
    msb = msb + (weconfig.CGM_EXT << 6)
    msb = msb + (I_MUX_OUT << 7)
    return msb , lsb

def analog_to_binary(vin,vref):
    '''
        Convert analog voltage to binary code for DAC
        vin: input voltage (mV)
        vref: reference voltage (mV)
    '''
    code = int((vin / vref) * 1024)
    #expand to 16-bit
    code = code << 6
    return code

def binary_to_one_hot(bin,num):
    '''
        Convert binary to one-hot encoding
        bin: binary input (1 to num)
        num: total number of bits
    '''
    one_hot = 1
    one_hot = one_hot << (bin-1)
    return one_hot

def binary_to_thermo(bin):
    '''
        Convert binary to thermometer encoding
        bin: binary input (0 to n)
    '''
    thermo = 0
    for i in range(bin):
        thermo = thermo << 1
        thermo = thermo + 1
    return thermo


if __name__ == '__main__':
    #For scenario where this code is being run as the main code. Debug purpose only.
    [msb,lsb] = gen_config_code(0,0,0,0)
    
    data_lsb = bin(lsb)[2:].zfill(32)
    data_msb = bin(msb)[2:].zfill(32)
    print(f"{data_lsb}")
    print(f"{data_msb}")
