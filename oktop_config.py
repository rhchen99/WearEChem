# oktop_config.py
# Combined ASIC config + OKTOP endpoint map

# ----- Bitfile -----
BITFILE = "weok.bit"

# ------------------------------
# ASIC MODE / CONFIG CONSTANTS
# ------------------------------
VREF_MV = 2560.0  # DAC reference (mV)

# DAC CONFIG
CGM_EXT = 0  # 0 = internal const-gm ref, 1 = external

# ADC CONFIG
ADC_OTA1 = 1          # 0..2
ADC_OTA2 = 1          # 0..2
ADC_STARTUP_SEL = 0   # 0..3 (we pack into 3 bits)
ADC_C2 = 2            # 0..4 (we pack into 4 bits)

# PSTAT CONFIG (enables)
PSTAT_S_BIAS   = 0
PSTAT_S_CC     = 0
PSTAT_S_OTAW   = 0
PSTAT_S_CLSABW = 0
PSTAT_S_OTAR   = 0
PSTAT_S_CLSABR = 0
PSTAT_S_SRE    = 0

# PSTAT 2x-current switches
PSTAT_OTAWI2X   = 0
PSTAT_OTARI2X   = 0
PSTAT_CLSABWI2X = 0
PSTAT_CLSABRI2X = 0

# CC CONFIG
CC_GAIN = 1   # 0 -> 10x, 1 -> 1x, 2 -> 0.1x, etc.
CC_SEL  = 5   # 1..11, packed as 5 bits

# MODE DEFINITIONS (high-level lab “modes” if you want them later)
MODE_DEFAULT = 0
MODE_PM      = 1
MODE_PSTAT   = 2
MODE_ADC     = 3
MODE_ION     = 4

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

# WireIn 0x09–0x0E : ASIC config packing (matches HDL asic_word)
#   asic_word = {
#       wi0C[4:0],      // ADC OTA settings
#       wi0D[2:0],      // ADC startup sel
#       wi0D[7:4],      // ADC C2
#       wi09[6:0],      // PSTAT block enables
#       wi0A[3:0],      // I2X switches
#       wi0B[2:0],      // CC gain
#       wi0B[11:7],     // CC sel (5 bits)
#       wi0E[0],        // CGM_EXT
#       8'd0            // pad
#   }
EP_WI_PSTAT_EN  = 0x09  # wi09
EP_WI_PSTAT_I2X = 0x0A  # wi0A
EP_WI_CC_CFG    = 0x0B  # wi0B
EP_WI_ADC_OTA   = 0x0C  # wi0C
EP_WI_ADC_MISC  = 0x0D  # wi0D
EP_WI_CGM_EXT   = 0x0E  # wi0E

# WireOut 0x20 : status
EP_WO_STATUS = 0x20
STATUS_DONE_SPI_BIT  = 1 << 0
STATUS_DONE_TASK_BIT = 1 << 1

EP_WO_SPI_CNT = 0x21
EP_WO_TSK_CNT = 0x22

# TriggerIn 0x40
EP_TI_MAIN       = 0x40
TRIG_CONFIG_BIT  = 1 << 0   # maps to trigger_config
TRIG_TASK_BIT    = 1 << 1   # maps to trigger_task

# TriggerOut 0x60
EP_TO_MAIN         = 0x60
TRIG_TASK_DONE_BIT = 1 << 0  # task_done_pulse

# PipeIn
EP_PI_CONFIG_MSB   = 0x80   # config MSB
EP_PI_CONFIG_LSB   = 0x81   # config LSB
EP_PI_WAVEFORM     = 0x82   # waveform FIFO
EP_PI_TST_IN       = 0x83   # test input FIFO (for debug)

# PipeOut
EP_PO_SPI_OUT_MSB = 0xA0    # SPI output MSB FIFO
EP_PO_SPI_OUT_LSB = 0xA1    # SPI output MSB FIFO
EP_PO_ADC_OUT     = 0xA2    # ADC output FIFO
EP_PO_TST_OUT     = 0xA3    # test output FIFO (for debug)
