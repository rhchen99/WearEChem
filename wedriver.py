import struct
import weconfig

def analog_to_binary(vin,vref):
    #convert analog input to 10-bit binary code
    code = int((vin / vref) * 1024)
    #expand to 16-bit
    code = code << 6
    return code

def binary_to_one_hot(bin,num):
    one_hot = 1
    one_hot = one_hot << (bin-1)
    return one_hot

def gen_config_code():
    '''
        generate 36-bit config code to be sent to SPI0
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
    code = code + (weconfig.ADC_MUX << 24)
    code = code + (weconfig.ADC_C2 << 26)
    code = code + (weconfig.ADC_STARTUP_SEL << 30)
    code = code + (weconfig.ADC_OTA2 << 32)
    code = code + (weconfig.ADC_OTA1 << 34)
    return code

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

def config_timing(teq,t1,t2):
    return 1


if __name__ == '__main__':
    #For scenario where this code is being run as the main code. Debug purpose
    #data = gen_ramp(200,100,-5)
    #data = gen_cv(100,200,100,5)
    #data = gen_dpv(1500,2000,5,100)
    # Pack data into bytes (little-endian 16-bit)
    #data_bytes = b''.join(struct.pack('<H', x) for x in data)
    
    data = gen_config_code()
    data = bin(data)[2:]
    data = data.zfill(36)

    print(f"{data}")
