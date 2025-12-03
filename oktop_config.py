# oktop_config.py
# Combined ASIC config + OKTOP endpoint map

# ----- Bitfile -----
BITFILE = "weok_fpga_ldo1.bit"

# ------------------------------
# ASIC MODE / CONFIG CONSTANTS
# ------------------------------
VREF_MV = 2560.0  # DAC reference (mV)

FIFO_DEPTH = 131072  # depth of the ADC ping-pong FIFOs (must match HDL)

# ------------------------------
# OKTOP ENDPOINT MAP
# ------------------------------

# WireIn 0x00: reset + mode bits
EP_WI_CTRL = 0x00
CTRL_RST_BIT       = 1 << 0  # reset
CTRL_TASK_MODE_BIT = 1 << 1  # task_mode
CTRL_DAC_MODE_BIT  = 1 << 2  # dac_mode
CTRL_ADC_MODE_BIT  = 1 << 3  # adc_mode

# WireIn 0x01–0x05 : DAC Settings
EP_WI_DAC_T1   = 0x01
EP_WI_DAC_T2   = 0x02
EP_WI_DAC_TS1  = 0x03
EP_WI_DAC_TS2  = 0x04
EP_WI_DAC_NSAM = 0x05

# WireIn 0x06–0x08 : ADC Timings
EP_WI_ADC_TWAKE   = 0x06
EP_WI_ADC_TSAMPLE = 0x07
EP_WI_ADC_NSAM    = 0x08

# WireIn 0x09 : SYSTEM_SPI
EP_WI_SYSTEM_SPI = 0x09
CTRL_IMUX_OUT_BIT = 1 << 3  # I_MUX_OUT
CTRL_CGM_EXT_BIT  = 1 << 2  # CGM_EXT
CTRL_ION_EN_BIT   = 1 << 1  # ION_EN
CTRL_PM_EN_BIT    = 1 << 0  # PM_EN

# WireIn 0x0A : ADC OTA1
EP_WI_ADC_OTA1 = 0x0A
# WireIn 0x0B : ADC OTA2
EP_WI_ADC_OTA2 = 0x0B
# WireIn 0x0C : ADC STARTUP SEL
EP_WI_ADC_STARTUP_SEL = 0x0C
# WireIn 0x0D : ADC C2
EP_WI_ADC_C2 = 0x0D
# WireIn 0x0E : ADC MUX
EP_WI_ADC_MUX = 0x0E

# WireIn 0x0F : PSTAT ENABLES
EP_WI_PSTAT_EN = 0x0F
CTRL_BIT_PSTAT_S_BIAS    = 1 << 6
CTRL_BIT_PSTAT_S_CC      = 1 << 5
CTRL_BIT_PSTAT_S_OTAW    = 1 << 4
CTRL_BIT_PSTAT_S_CLSABW  = 1 << 3
CTRL_BIT_PSTAT_S_OTAR    = 1 << 2
CTRL_BIT_PSTAT_S_CLSABR  = 1 << 1
CTRL_BIT_PSTAT_S_SRE     = 1 << 0

# WireIn 0x10 : PSTAT 2x-current switches
EP_WI_PSTAT_I2X = 0x10
CTRL_BIT_PSTAT_OTAWI2X    = 1 << 3
CTRL_BIT_PSTAT_OTARI2X    = 1 << 2
CTRL_BIT_PSTAT_CLSABWI2X  = 1 << 1
CTRL_BIT_PSTAT_CLSABRI2X  = 1 << 0

# WireIn 0x11 : CC GAIN
EP_WI_CC_GAIN = 0x11
# WireIn 0x12 : CC SEL
EP_WI_CC_SEL = 0x12

# WireIn 0x13 : LDO Enable
EP_WI_LDO_EN = 0x13
LDO_BIT_VREFDAC = 1<<0
LDO_BIT_WEGD = 1<<1
LDO_BIT_AVDD3V0 = 1<<2
LDO_BIT_VCM = 1<<3
LDO_BIT_ION3V0 = 1<<4
LDO_BIT_ION1V8 = 1<<5
LDO_BIT_DVDD1V8 = 1<<6
LDO_BIT_AVDD1V8 = 1<<7

# WireOut 0x20 : status
EP_WO_STATUS = 0x20
STATUS_DONE_SPI_BIT  = 1 << 0
STATUS_DONE_TASK_BIT = 1 << 1

# WireOut 0x21–0x22 : counters
EP_WO_SPI_CNT = 0x21
EP_WO_TSK_CNT = 0x22

# TriggerIn 0x40
EP_TI_MAIN       = 0x40
TRIG_CONFIG_BIT  = 0   # maps to trigger_config
TRIG_TASK_BIT    = 1   # maps to trigger_task

# TriggerOut 0x60
EP_TO_MAIN          = 0x60
TRIG_TASK_DONE_BIT  = 1      # task_done_pulse
TRIG_FIFO_FLIP_BIT  = 2     # fifo_flip_pulse

# PipeIn
EP_PI_WAVEFORM     = 0x80   # waveform FIFO
EP_PI_TST_IN       = 0x83   # test input FIFO (for debug)

# PipeOut
EP_PO_SPI_OUT_MSB = 0xA0    # SPI output MSB FIFO
EP_PO_SPI_OUT_LSB = 0xA1    # SPI output MSB FIFO
EP_PO_ADC_OUT     = 0xA2    # ADC output FIFO
EP_PO_TST_OUT     = 0xA3    # test output FIFO (for debug)
