'''
This is the configuration file for the WearEChem project.
Renhe Chen (rec004@ucsd.edu)
University of California San Diego
'''
# DAC CONFIG
VREF = 2560             #reference voltage for DAC (mV)

CGM_EXT = 0             # 0 to enable constant gm internal refrence, 1 to use external

# ADC CONFIG
ADC_OTA1 = 1            # from 0 to 2 (will be thermo encoded)
ADC_OTA2 = 1            # from 0 to 2 (will be thermo encoded)
ADC_STARTUP_SEL = 0     # from 0 to 3
ADC_C2 = 2              # from 0 to 4 (will be thermo encoded)

# PSTAT CONFIG
# below are single-bit switches to enable/disable PSTAT blocks
PSTAT_S_BIAS = 0        # bias
PSTAT_S_CC = 0          # current conveyor
PSTAT_S_OTAW = 0        # working electrode OTA
PSTAT_S_CLSABW = 0      # working electrode second stage
PSTAT_S_OTAR = 0        # reference electrode OTA
PSTAT_S_CLSABR = 0      # reference electrode second stage
PSTAT_S_SRE = 0         # slew rate enhancement

# 2x current switch for PSTAT blocks
PSTAT_OTAWI2X = 0
PSTAT_OTARI2X = 0
PSTAT_CLSABWI2X = 0
PSTAT_CLSABRI2X = 0

# CC CONFIG
CC_GAIN = 1             # set CC gain. 0 -> 10x, 1 -> 1x, 2 -> 0.1x
CC_SEL = 5              # select CC device, range from 1 to 11. default is 5

#mode definition
MODE_DEFAULT = 0
MODE_PM = 1
MODE_PSTAT = 2
MODE_ADC = 3
MODE_ION = 4

# Opal Kelly Endpoint Configuration

# FPGA RST ALL Wire
RST_ALL = 0x10         # reset all

SYS_TRIG = 0x20        # system trigger

# FPGA SPI CONFIG
SPI_TRIG = 0x40        # spi trigger
SPI_IN = 0x80          # spi input buffer (pipein)
SPI_OUT = 0xA0         # spi output buffer (pipeout)

# FPGA ADC CONFIG
ADC_ENABLE = 0x60       # adc enable register
ADC_TSAM = 0x20         # adc sample time register
ADC_TWAKE = 0x00        # adc wakeup time register
ADC_NSAM = 0x50         # adc number of samples register
ADC_OUT = 0xB0          # adc output buffer (pipeout)

# FPGA DAC CONFIG
DAC_ENABLE = 0x70       # dac enable register
DAC_IN = 0x90           # dac input buffer (pipein)
DAC_MODE = 0x30         # dac mode register
DAC_T1 = 0xC0           # dac timing register 1
DAC_T2 = 0xD0           # dac timing register 2
DAC_NSAM = 0xE0         # dac number of samples register
