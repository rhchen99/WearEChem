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

def adc_config(tsam,twake,nsam):
    '''
        confige ADC settings
        tsam: ADC sample time (16 bits)
        twake: ADC wakeup time (16 bits)
        nsam: ADC number of samples (16 bits)
    '''
    #set ADC_TSAM register
    dev.SetWireInValue(weconfig.ADC_TSAM, tsam)
    #set ADC_TWAKE register
    dev.SetWireInValue(weconfig.ADC_TWAKE, twake)
    #set ADC_NSAM register
    dev.SetWireInValue(weconfig.ADC_NSAM, nsam)
    dev.UpdateWireIns()
    #read back and print the settings
    tsam_out = dev.GetWireOutValue(weconfig.ADC_TSAM)
    twake_out = dev.GetWireOutValue(weconfig.ADC_TWAKE)
    nsam_out = dev.GetWireOutValue(weconfig.ADC_NSAM)
    print(f"ADC configuration complete.\nsampling time: {tsam_out}\nwakeup time: {twake_out}\nnumber of samples: {nsam_out}")

def dac_config(mode,t1,t2,nsam,data_list):
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
    #set DAC_NSAM register
    dev.SetWireInValue(weconfig.DAC_NSAM, nsam)
    dev.UpdateWireIns()
    #read back and print the mode
    mode_out = dev.GetWireOutValue(weconfig.DAC_MODE)
    print(f"DAC mode set to: {mode_out}")
    # Pack data into bytes
    dataout = b''.join(value.to_bytes(2, 'little') for value in data_list)
    # Load data to DAC buffer
    dev.WriteToPipeIn(weconfig.DAC_IN, dataout)
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

def spi_write(data):
    '''
    Write data to SPI interface and read the response.
    '''
    datain = 0
    # Pack data into bytes
    dataout = data.to_bytes(5, 'little')
    # Load data to SPI input buffer
    dev.WriteToPipeIn(weconfig.SPI_PIPE_IN, dataout)
    # Trigger SPI to send data into DUT
    dev.ActivateTriggerIn(weconfig.SPI_TRIG_IN, 0)
    time.sleep(0.1)
    # Trigger SPI again to pop out data
    dev.ActivateTriggerIn(weconfig.SPI_TRIG_IN, 0)
    time.sleep(0.1)
    # Read back from SPI output buffer
    datain = dev.ReadFromPipeOut(weconfig.SPI_PIPE_OUT, 5)
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
    data = gen_config_code(I_MUX_OUT, ION_EN, PM_EN, ADC_MUX)
    #send data to SPI
    spi_write(data)

def gen_config_code(I_MUX_OUT,ION_EN,PM_EN,ADC_MUX):
    '''
        assemble 40-bit config code to be sent to SPI0
        with settings from weconfig.py
    '''
    code = binary_to_one_hot(weconfig.CC_SEL,11)
    code = code + (weconfig.CC_GAIN << 11)
    code = code + (weconfig.PSTAT_CLSABRI2X << 13)
    code = code + (weconfig.PSTAT_CLSABWI2X << 14)
    code = code + (weconfig.PSTAT_OTARI2X << 15)
    code = code + (weconfig.PSTAT_OTAWI2X << 16)
    code = code + (weconfig.PSTAT_S_SRE << 17)
    code = code + (weconfig.PSTAT_S_CLSABR << 18)
    code = code + (weconfig.PSTAT_S_OTAR << 19)
    code = code + (weconfig.PSTAT_S_CLSABW << 20)
    code = code + (weconfig.PSTAT_S_OTAW << 21)
    code = code + (weconfig.PSTAT_S_CC << 22)
    code = code + (weconfig.PSTAT_S_BIAS << 23)
    code = code + (ADC_MUX << 24)
    code = code + (binary_to_thermo(weconfig.ADC_C2) << 26)
    code = code + (weconfig.ADC_STARTUP_SEL << 30)
    code = code + (binary_to_thermo(weconfig.ADC_OTA2) << 32)
    code = code + (binary_to_thermo(weconfig.ADC_OTA1) << 34)
    code = code + (PM_EN << 35)
    code = code + (ION_EN << 36)
    code = code + (weconfig.CGM_EXT << 37)
    code = code + (I_MUX_OUT << 38)
    return code

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
    data = gen_config_code(0,0,0,0)
    dataout = data.to_bytes(5, 'little')
    databin = bin(data)[2:].zfill(40)
    print(f"{databin}")
    print(f"{dataout}")
