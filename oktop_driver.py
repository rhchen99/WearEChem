# oktop_driver.py
#
# Python-side driver for the OKTOP / WETOP design.
# Uses Opal Kelly FrontPanel Python API (ok.py) and the endpoint
# definitions in oktop_config.py.
import time
import ok
import oktop_config as cfg

class OKTop:
    def __init__(self, bitfile: str, serial: str = ""):
        self.dev = ok.okCFrontPanel()
        self.bitfile = bitfile
        self.serial = serial
        # Shadow for control WireIn (0x00)
        self._ctrl_shadow = 0
        # Shadow for SYSTEM_SPI WireIn (0x09)
        self._spi_shadow = 0
        # Shadow for PSTAT ENABLES WireIn (0x0F)
        self._pstat_shadow = 0
        # Shadow for PSTAT 2x current (0x10)
        self._pstat_i2x_shadow = 0
        # Shadow for LDO ENABLE (0x13)
        self._ldo_en_shadow = 0

    # ---------------------------------------------------------------------
    # Low-level helpers / device init
    # ---------------------------------------------------------------------
    def open_and_configure(self):
        """Open the device and configure the FPGA with the given bitfile."""
        print("Opening + configuring FPGA...")
        if self.dev.OpenBySerial(self.serial) != 0:

            raise RuntimeError("Failed to open Opal Kelly device (check USB / drivers / cable).")

        self.dev.ResetFPGA()
        err = self.dev.ConfigureFPGA(self.bitfile)
        if err != 0:
            raise RuntimeError(f"ConfigureFPGA failed with error code {err}")

        if not self.dev.IsFrontPanelEnabled():
            raise RuntimeError("FrontPanel is not enabled after configuration.")

        print("FPGA configured and FrontPanel enabled.")

    def _update_ctrl(self):
        """Push the current control-word shadow to WireIn 0x00."""
        self.dev.SetWireInValue(cfg.EP_WI_CTRL, self._ctrl_shadow & 0xFFFF)
        self.dev.UpdateWireIns()

    def _update_sys_spi(self):
        """Push the current control-word shadow to WireIn 0x00."""
        self.dev.SetWireInValue(cfg.EP_WI_SYSTEM_SPI, self._spi_shadow & 0xFFFF)
        self.dev.UpdateWireIns()
    
    def _update_pstat_slp(self):
        """Push the current control-word shadow to WireIn 0x0F."""
        self.dev.SetWireInValue(cfg.EP_WI_PSTAT_EN, self._pstat_shadow & 0xFFFF)
        self.dev.UpdateWireIns()
    
    def _update_pstat_i2x(self):
        """Push the current control-word shadow to WireIn 0x10."""
        self.dev.SetWireInValue(cfg.EP_WI_PSTAT_I2X, self._pstat_i2x_shadow & 0xFFFF)
        self.dev.UpdateWireIns()
    
    def _update_ldo_en(self):
        """Push the current LDO ENABLE shadow to WireIn 0x13."""
        self.dev.SetWireInValue(cfg.EP_WI_LDO_EN, self._ldo_en_shadow & 0xFFFF)
        self.dev.UpdateWireIns()

    def set_ctrl_bits(self, mask: int, value: bool):
        """Set or clear bits in the control word (WireIn 0x00)."""
        if value:
            self._ctrl_shadow |= mask
        else:
            self._ctrl_shadow &= ~mask
        self._update_ctrl()

    def pulse_ctrl_bit(self, mask: int, pulse_time: float = 0.0):
        """Generate a simple high-then-low pulse on a control bit."""
        self.set_ctrl_bits(mask, True)
        if pulse_time > 0:
            time.sleep(pulse_time)
        self.set_ctrl_bits(mask, False)

    def set_sys_spi(self, mask: int, value: bool):
        """Set or clear bits in the control word (WireIn 0x00)."""
        if value:
            self._spi_shadow |= mask
        else:
            self._spi_shadow &= ~mask
        self._update_sys_spi()
    
    def set_pstat_slp(self, mask: int, value: bool):
        """Set or clear bits in the PSTAT ENABLES word (WireIn 0x0F)."""
        if value:
            self._pstat_shadow |= mask
        else:
            self._pstat_shadow &= ~mask
        self._update_pstat_slp()
    
    def set_pstat_i2x(self, mask: int, value: bool):
        """Set or clear bits in the PSTAT 2x current word (WireIn 0x10)."""
        if value:
            self._pstat_i2x_shadow |= mask
        else:
            self._pstat_i2x_shadow &= ~mask
        self._update_pstat_i2x()
    
    def set_ldo_en(self, mask: int, value: bool):
        """Set or clear bits in the LDO ENABLE word (WireIn 0x13)."""
        if value:
            self._ldo_en_shadow |= mask
        else:
            self._ldo_en_shadow &= ~mask
        self._update_ldo_en()

    # ---------------------------------------------------------------------
    # High-level system control
    # ---------------------------------------------------------------------
    def system_reset(self):
        """Reset the system via WireIn 0x00 bit0."""
        print("Asserting reset...")
        self.pulse_ctrl_bit(cfg.CTRL_RST_BIT, pulse_time=0.1)
        print("Reset done.")

    def set_modes(self, task_mode: int, dac_mode: int, adc_mode: int):
        """
        Set the mode bits in WireIn 0x00.
        task_mode: 0/1
        dac_mode : 0/1
        adc_mode : 0/1
        """
        print("Setting modes...")
        self.set_ctrl_bits(cfg.CTRL_TASK_MODE_BIT, bool(task_mode))
        self.set_ctrl_bits(cfg.CTRL_DAC_MODE_BIT,  bool(dac_mode))
        self.set_ctrl_bits(cfg.CTRL_ADC_MODE_BIT,  bool(adc_mode))
        print("Modes set.")

    def set_force_awake(self, force_awake: int):
        """
        Set the force_awake bit in WireIn 0x00.
        force_awake: 0/1
        """
        print("Setting force_awake...")
        self.set_ctrl_bits(cfg.CTRL_FORCE_AWAKE_BIT, bool(force_awake))
        print("force_awake set.")
    
    # ---------------------------------------------------------------------
    # DAC / ADC configuration (WireIns)
    # ---------------------------------------------------------------------
    def config_dac(self, t1: int, t2: int, ts1: int, ts2: int, nsam: int):
        """Write DAC timing parameters into WireIns."""
        print("Writing DAC configs...")
        self.dev.SetWireInValue(cfg.EP_WI_DAC_T1,   t1 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_T2,   t2 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_TS1,  ts1 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_TS2,  ts2 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_NSAM, nsam & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print("DAC config written.")

    def config_adc(self, twake: int, tsample: int, nsam: int):
        """Write ADC timing parameters into WireIns."""
        print("Writing ADC configs...")
        self.dev.SetWireInValue(cfg.EP_WI_ADC_TWAKE,   twake & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_TSAMPLE, tsample & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_NSAM,    nsam & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print("ADC config written.")

    
    # ---------------------------------------------------------------------
    # Utilities for packing/unpacking
    # ---------------------------------------------------------------------
    @staticmethod
    def _u32_to_bytes_le(value: int) -> bytes:
        return int(value & 0xFFFFFFFF).to_bytes(4, byteorder="little", signed=False)

    def complete_to_multiple_of_4(self,lst):
        '''
            Pad the list to a multiple of 4 by repeating the last item
        '''
        remainder = len(lst) % 4
        for i in range(4 - remainder):
            lst.append(lst[-1])  # repeat last item
        return lst

    def binary_to_one_hot(self,bin,num):
        '''
            Convert binary to one-hot encoding
            bin: binary input (1 to num)
            num: total number of bits
        '''
        one_hot = 1
        one_hot = one_hot << (bin-1)
        return one_hot

    def binary_to_thermo(self,bin):
        '''
            Convert binary to thermometer encoding
            bin: binary input (0 to n)
        '''
        thermo = 0
        for i in range(bin):
            thermo = thermo << 1
            thermo = thermo + 1
        return thermo

    def analog_to_binary(self,vin,vref):
        '''
            Convert analog voltage to binary code for DAC
            vin: input voltage (mV)
            vref: reference voltage (mV)
        '''
        code = int((vin / vref) * 1024)
        return code
    
    # ---------------------------------------------------------------------
    # SPI settings through WireIns
    # ---------------------------------------------------------------------
    def set_imux_out(self, imux_out: int):
        """Set the I_MUX_OUT via WireIn 0x09."""
        self.set_sys_spi(cfg.CTRL_IMUX_OUT_BIT, bool(imux_out))
        print(f"I_MUX_OUT set to {imux_out}.")
    
    def set_cgm_ext(self, cgm_ext: int):
        """Set the CGM_EXT via WireIn 0x09."""
        self.set_sys_spi(cfg.CTRL_CGM_EXT_BIT, bool(cgm_ext))
        print(f"CGM_EXT set to {cgm_ext}.")
    
    def set_ion_en(self, ion_en: int):
        """Set the ION_EN via WireIn 0x09."""
        self.set_sys_spi(cfg.CTRL_ION_EN_BIT, bool(ion_en))
        print(f"ION_EN set to {ion_en}.")

    def set_pm_en(self, pm_en: int):
        """Set the PM_EN via WireIn 0x09."""
        self.set_sys_spi(cfg.CTRL_PM_EN_BIT, bool(pm_en))
        print(f"PM_EN set to {pm_en}.")

    def set_cc_gain(self, gain):
        """Set the CC gain via WireIn 0x11."""
        if gain not in (1, 10, 0.1):
            raise ValueError("Gain must be 0.1, 1 or 10.")
        else:
            if gain == 10:
                bin = 0
            elif gain == 1:
                bin = 1
            elif gain == 0.1:
                bin = 2
        self.dev.SetWireInValue(cfg.EP_WI_CC_GAIN, bin & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print(f"CC gain set to {gain}.")
    
    def set_cc_sel(self, sel: int):
        """Set the CC selection via WireIn 0x12."""
        if not (1 <= sel <= 11):
            raise ValueError("CC selection must be between 1 and 11.")
        one_hot = self.binary_to_one_hot(sel,11)
        self.dev.SetWireInValue(cfg.EP_WI_CC_SEL, one_hot & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print(f"CC selection set to {sel}.")
    
    def set_adc_mux(self, mux: int):
        """Set the ADC MUX via WireIn 0x0E."""
        self.dev.SetWireInValue(cfg.EP_WI_ADC_MUX, mux & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print(f"ADC MUX set to {mux}.")
    
    def set_adc_ota1(self, ota1: int):
        """Set the ADC OTA1 via WireIn 0x0A."""
        thermo = self.binary_to_thermo(ota1)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_OTA1, thermo & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print(f"ADC OTA1 set to {ota1}.")
    
    def set_adc_ota2(self, ota2: int):
        """Set the ADC OTA2 via WireIn 0x0B."""
        thermo = self.binary_to_thermo(ota2)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_OTA2, thermo & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print(f"ADC OTA2 set to {ota2}.")
    
    def set_adc_startup_sel(self, sel: int):
        """Set the ADC STARTUP SEL via WireIn 0x0C."""
        self.dev.SetWireInValue(cfg.EP_WI_ADC_STARTUP_SEL, sel & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print(f"ADC STARTUP SEL set to {sel}.")
    
    def set_adc_c2(self, c2: int):
        """Set the ADC C2 via WireIn 0x0D."""
        thermo = self.binary_to_thermo(c2)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_C2, thermo & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print(f"ADC C2 set to {c2}.")
    
    def set_pstat_sleep(self, bias: int, cc: int, otaw: int, clsabw: int, otar: int, clsabr: int, sre: int):
        """Set the PSTAT ENABLES via WireIn 0x0F."""
        self.set_pstat_slp(cfg.CTRL_BIT_PSTAT_S_BIAS,    bool(bias))
        self.set_pstat_slp(cfg.CTRL_BIT_PSTAT_S_CC,      bool(cc))
        self.set_pstat_slp(cfg.CTRL_BIT_PSTAT_S_OTAW,    bool(otaw))
        self.set_pstat_slp(cfg.CTRL_BIT_PSTAT_S_CLSABW,  bool(clsabw))
        self.set_pstat_slp(cfg.CTRL_BIT_PSTAT_S_OTAR,    bool(otar))
        self.set_pstat_slp(cfg.CTRL_BIT_PSTAT_S_CLSABR,  bool(clsabr))
        self.set_pstat_slp(cfg.CTRL_BIT_PSTAT_S_SRE,     bool(sre))
        self.dev.UpdateWireIns()
        print(f"PSTAT ENABLES set.")
    
    def set_pstat_i2x_all(self, otaw: int, otar: int, clsabw: int, clsabr: int):
        """Set the PSTAT 2x-current switches via WireIn 0x10."""
        self.set_pstat_i2x(cfg.CTRL_BIT_PSTAT_OTAWI2X,    bool(otaw))
        self.set_pstat_i2x(cfg.CTRL_BIT_PSTAT_OTARI2X,    bool(otar))
        self.set_pstat_i2x(cfg.CTRL_BIT_PSTAT_CLSABWI2X,  bool(clsabw))
        self.set_pstat_i2x(cfg.CTRL_BIT_PSTAT_CLSABRI2X,  bool(clsabr))
        self.dev.UpdateWireIns()
        print(f"PSTAT 2x-current switches set.")

    def set_ldo_en_all(self, vrefdac: int, wegd: int, avdd3v0: int, vcm: int, ion3v0: int, ion1v8: int, dvdd1v8: int, avdd1v8: int):
        """Set the LDO ENABLE via WireIn 0x13."""
        self.set_ldo_en(cfg.LDO_BIT_VREFDAC,  bool(vrefdac))
        self.set_ldo_en(cfg.LDO_BIT_WEGD,     bool(wegd))
        self.set_ldo_en(cfg.LDO_BIT_AVDD3V0,  bool(avdd3v0))
        self.set_ldo_en(cfg.LDO_BIT_VCM,      bool(vcm))
        self.set_ldo_en(cfg.LDO_BIT_ION3V0,   bool(ion3v0))
        self.set_ldo_en(cfg.LDO_BIT_ION1V8,   bool(ion1v8))
        self.set_ldo_en(cfg.LDO_BIT_DVDD1V8,  bool(dvdd1v8))
        self.set_ldo_en(cfg.LDO_BIT_AVDD1V8,  bool(avdd1v8))
        self.dev.UpdateWireIns()
        print(f"LDO ENABLE set.")

    # ---------------------------------------------------------------------
    # SPI configuration trigger
    # ---------------------------------------------------------------------
    def trigger_spi_config(self):
        """
        Kick off the SPI/config FSM via TriggerIn 0x40, bit0.
        """
        print("Triggering SPI configuration...")
        for i in range(2):
            self.dev.ActivateTriggerIn(cfg.EP_TI_MAIN, cfg.TRIG_CONFIG_BIT)
        print("SPI/config trigger sent.")

    def config_through_spi(self):
        """Trigger SPI configuration and wait for completion."""
        self.trigger_spi_config()
        self.read_spi_cnt()
        msb = self.read_spi_out_msb(4)
        lsb = self.read_spi_out_lsb(4)
        print("SPI out (MSB) words:", [hex(x) for x in msb])
        print("SPI out (LSB) words:", [hex(x) for x in lsb])

        
    # ---------------------------------------------------------------------
    # Waveform generation
    # ---------------------------------------------------------------------
    def gen_ramp(self,vstart,vstop,vstep):
        '''
            vstart: starting voltage (mV)
            vstop: final voltage (mV)
            vstep: step voltage (mV)
        '''
        print("Generating ramp waveform...")
        data = []
        steps = int((vstop-vstart)/vstep + 1)
        for i in range(steps):
            v = vstart + i * vstep
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        print(f"Generated waveform with {len(data)} samples.")
        return data

    def gen_cv(self,vstart,v1,v2,vstep):
        '''
            vstart: starting voltage (mV)
            v1: CV turning point1 (mV)
            v2: CV turning point2 (mV)
            vstep: step voltage (mV)
        '''
        print("Generating CV waveform...")
        data = []
        steps = int((v1-vstart)/vstep)
        for i in range(steps):
            v = vstart + i * vstep
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        steps = int((v1-v2)/vstep + 1)
        for i in range(steps):
            v = v1 - i * vstep
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        print(f"Generated waveform with {len(data)} samples.")
        return data

    def gen_dpv(self,vstart,vstop,vstep,vpulse):
        '''
            vstart: starting voltage (mV)
            vstop: final voltage (mV)
            vstep: step voltage (mV)
            vpulse: DPV pulse height (mV)
        '''
        print("Generating DPV waveform...")
        data = []
        steps = int((vstop-vstart)/vstep + 1)
        for i in range(steps):
            v = vstart + i * vstep
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
            v = vstart + i * vstep + vpulse
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        print(f"Generated waveform with {len(data)} samples.")
        return data
    # ---------------------------------------------------------------------
    # Waveform FIFO
    # ---------------------------------------------------------------------
    def write_waveform_words(self, words32):
        """
        Write a list of 32-bit integers into the waveform FIFO via PipeIn 0x81.
        """
        print("Writing waveform data to FIFO...")
        data = self.complete_to_multiple_of_4(words32)
        buf = bytearray()        
        for x in data:
            buf += self._u32_to_bytes_le(x)        
        self.dev.WriteToPipeIn(cfg.EP_PI_WAVEFORM, buf)
        print(f"Wrote {len(words32)} words to waveform FIFO.")

    # ---------------------------------------------------------------------
    # Task trigger + completion
    # ---------------------------------------------------------------------
    def trigger_task(self):
        """Kick off the 'task' FSM via TriggerIn 0x40, bit1."""
        print("Triggering task...")
        self.dev.ActivateTriggerIn(cfg.EP_TI_MAIN, cfg.TRIG_TASK_BIT)
        print("Task trigger sent.")

    def wait_for_task_done(self, timeout_s: float = 1.0) -> bool:
        """
        Poll TriggerOut 0x60 bit0 for task-done pulse.
        Returns True if seen, False on timeout.
        """
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            self.dev.UpdateTriggerOuts()
            if self.dev.IsTriggered(cfg.EP_TO_MAIN, cfg.TRIG_TASK_DONE_BIT):
                print("Task done trigger observed.")
                return True
            time.sleep(0.001)
        print("Timeout waiting for task done trigger.")
        return False
    
    def task_watcher(self):
        """update the triggers"""
        data = []
        while True:
            self.dev.UpdateTriggerOuts()
            if self.dev.IsTriggered(cfg.EP_TO_MAIN, cfg.TRIG_TASK_DONE_BIT):
                print("Task done trigger observed.")
                self.trigger_flip()
                data.extend(self.read_adc_out(cfg.FIFO_DEPTH))
                return data
            if self.dev.IsTriggered(cfg.EP_TO_MAIN, cfg.TRIG_FIFO_FLIP_BIT):
                data.extend(self.read_adc_out(cfg.FIFO_DEPTH))
                data.pop()
            time.sleep(0.001)
    # ---------------------------------------------------------------------
    # ADC Ping-pong FIFO Flip
    # ---------------------------------------------------------------------
    def trigger_flip(self):
        """flip the ADC output ping-pong fifo."""
        self.dev.ActivateTriggerIn(cfg.EP_TI_MAIN, 2)
        print("FIFO flipped.")
    # ---------------------------------------------------------------------
    # Reading from SPI/ADC FIFOs (PipeOuts)
    # ---------------------------------------------------------------------
    def read_spi_out_msb(self, n_words: int):
        """
        Read n_words of SPI output MSB data from PipeOut 0xA0.
        Returns list of ints.
        """
        n_bytes = n_words * 4
        buf = bytearray(n_bytes)
        got = self.dev.ReadFromPipeOut(cfg.EP_PO_SPI_OUT_MSB, buf)
        if got != n_bytes:
            print(f"Warning: expected {n_bytes} bytes, got {got}.")
        raw = bytes(buf[:got])
        words = [int.from_bytes(raw[i:i+4], "little") for i in range(0, len(raw), 4)]
        return words
    
    def read_spi_out_lsb(self, n_words: int):
        """
        Read n_words of SPI output LSB data from PipeOut 0xA1.
        Returns list of ints.
        """
        n_bytes = n_words * 4
        buf = bytearray(n_bytes)
        got = self.dev.ReadFromPipeOut(cfg.EP_PO_SPI_OUT_LSB, buf)
        if got != n_bytes:
            print(f"Warning: expected {n_bytes} bytes, got {got}.")
        raw = bytes(buf[:got])
        words = [int.from_bytes(raw[i:i+4], "little") for i in range(0, len(raw), 4)]
        return words

    def read_adc_out(self, n_words: int):
        """
        Read n_words of ADC output data from PipeOut 0xA2.
        Returns list of ints.
        """
        n_bytes = n_words * 4
        buf = bytearray(n_bytes)
        got = self.dev.ReadFromPipeOut(cfg.EP_PO_ADC_OUT, buf)
        if got != n_bytes:
            print(f"Warning: expected {n_bytes} bytes, got {got}.")
        raw = bytes(buf[:got])
        words = [int.from_bytes(raw[i:i+4], "little") for i in range(0, len(raw), 4)]
        return words
    # ---------------------------------------------------------------------
    # Status wire
    # ---------------------------------------------------------------------
    def read_status(self):
        """Read WireOut 0x20 and decode done flags."""
        self.dev.UpdateWireOuts()
        v = self.dev.GetWireOutValue(cfg.EP_WO_STATUS)
        done_spi = bool(v & cfg.STATUS_DONE_SPI_BIT)
        done_task = bool(v & cfg.STATUS_DONE_TASK_BIT)
        return {"raw": v, "done_spi": done_spi, "done_task": done_task}
    
    def read_spi_cnt(self):
        """Read WireOut 0x21."""
        self.dev.UpdateWireOuts()
        v = self.dev.GetWireOutValue(cfg.EP_WO_SPI_CNT)
        print(f"SPI triggered {v} times.")
        return {"raw": v}
    
    
# -------------------------------------------------------------------------
# Quick bring-up test harness
# -------------------------------------------------------------------------
if __name__ == "__main__":
    bitfile = cfg.BITFILE

    fpga = OKTop(bitfile)

    fpga.open_and_configure()

    fpga.system_reset()

    fpga.set_modes(task_mode=1, dac_mode=0, adc_mode=0)
    
    wav = fpga.gen_ramp(vstart=2400, vstop=2560, vstep=10)

    fpga.config_dac(t1=100, t2=200, ts1=50, ts2=50, nsam=len(wav))
    
    fpga.config_adc(twake=100, tsample=2**20, nsam=1)

    fpga.set_imux_out(0)
    fpga.set_cgm_ext(0)
    fpga.set_ion_en(0)
    fpga.set_pm_en(0)
    fpga.set_cc_gain(1)
    fpga.set_cc_sel(5)
    fpga.set_adc_mux(0)
    fpga.set_adc_ota1(1)
    fpga.set_adc_ota2(1)
    fpga.set_adc_startup_sel(0)
    fpga.set_adc_c2(2)

    fpga.set_pstat_sleep(bias=0, cc=0, otaw=0, clsabw=0, otar=0, clsabr=0, sre=0)
    fpga.set_pstat_i2x_all(otaw=0, otar=0, clsabw=0, clsabr=0)
    

    fpga.config_through_spi()

    fpga.write_waveform_words(wav)


    
    # ---------------------------------------------------------------
    #print("Triggering task...")
    fpga.trigger_task()
    data = fpga.task_watcher()

    spi_data_msb = fpga.read_spi_out_msb(4)
    spi_data_lsb = fpga.read_spi_out_lsb(4)

    print("SPI out (MSB) words:", [hex(x) for x in spi_data_msb])
    print("SPI out (LSB) words:", [hex(x) for x in spi_data_lsb])

    with open("output.csv", "w") as f:
        for item in data:
            f.write(f"{item}\n")
