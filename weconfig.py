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
RST_ALL = 0x00           # reset all

TASK_MODE = 0x01        # system mode select

# FPGA ADC CONFIG REGISTERS
ADC_MODE = 0x10         # adc mode register
ADC_TWAKE = 0x11        # adc wakeup time register
ADC_TSAM = 0x12         # adc sample time register
ADC_NSAM = 0x13         # adc number of samples register

# FPGA DAC CONFIG REGISTERS
DAC_MODE = 0x14         # dac mode register
DAC_T1 = 0x15           # dac timing register 1
DAC_T2 = 0x16           # dac timing register 2
DAC_TS1 = 0x17           # dac timing register 1
DAC_TS2 = 0x18           # dac timing register 2
DAC_NSAM = 0x19         # dac number of samples register

#TriggerIn
TRIG_CONFIG = 0x40       # system config trigger
TRIG_TASK = 0x41         # system task trigger

# PipeIn Endpoints
SPI_WAV = 0x80    # SPI waveform data input
SPI_CONFIG_MSB = 0x90  # SPI config data MSB
SPI_CONFIG_LSB = 0xA0  # SPI config data LSB

# PipeOut Endpoints
ADC_OUT = 0xB0   # ADC data output
SPI_OUT_MSB = 0xC0  # SPI output data MSB
SPI_OUT_LSB = 0xD0  # SPI output data LSB
