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

    # ---------------------------------------------------------------------
    # SPI config FIFO + trigger (host 40-bit mode)
    # ---------------------------------------------------------------------
    def write_spi_config_word40(self, msb_32: int, lsb_32: int):
        '''Write a 40-bit SPI config word into the two PipeIns (0x80 and 0x81).'''
        print("Writing SPI config words to FIFO...")
        payload = self._u32_to_bytes_le(msb_32)
        buf = bytearray(payload*4)
        self.dev.WriteToPipeIn(cfg.EP_PI_CONFIG_MSB, buf)
        print("SPI config MSB sent via PipeIn.")

        payload = self._u32_to_bytes_le(lsb_32)
        buf = bytearray(payload*4)
        self.dev.WriteToPipeIn(cfg.EP_PI_CONFIG_LSB, buf)
        print("SPI config LSB sent via PipeIn.")
        

    def trigger_spi_config(self):
        """
        Kick off the SPI/config FSM via TriggerIn 0x40, bit0.
        """
        print("Triggering SPI configuration...")
        for i in range(4):
            self.dev.ActivateTriggerIn(cfg.EP_TI_MAIN, cfg.TRIG_CONFIG_BIT)
        print("SPI/config trigger sent.")

    # ---------------------------------------------------------------------
    # Waveform FIFO
    # ---------------------------------------------------------------------
    def write_waveform_words(self, words32):
        """
        Write a list of 32-bit integers into the waveform FIFO via PipeIn 0x81.
        """
        print("Writing waveform data to FIFO...")
        data = self.complete_to_multiple_of_16(words32)
        buf = bytearray()        
        for x in data:
            buf += self._u32_to_bytes_le(x)        
        self.dev.WriteToPipeIn(cfg.EP_PI_WAVEFORM, buf)
        print(f"Wrote {len(words32)} words to waveform FIFO.")

    
    # ---------------------------------------------------------------------
    # FIFO control
    # ---------------------------------------------------------------------
    def trigger_flip(self):
        """flip the ADC output ping-pong fifo."""
        self.dev.ActivateTriggerIn(cfg.EP_TI_MAIN, 2)
        print("FIFO flipped.")
    
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
    # Reading from SPI / ADC FIFOs (PipeOuts)
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
    # ---------------------------------------------------------------------
    #
    # ---------------------------------------------------------------------
    
    def gen_config_code(self,I_MUX_OUT,ION_EN,PM_EN,ADC_MUX):
        '''
            assemble 40-bit config code to be sent to SPI0
            with settings from weconfig.py
        '''
        print("Generating SPI config code...")
        lsb = self.binary_to_one_hot(cfg.CC_SEL,11)
        lsb = lsb + (cfg.CC_GAIN << 11)
        lsb = lsb + (cfg.PSTAT_CLSABRI2X << 13)
        lsb = lsb + (cfg.PSTAT_CLSABWI2X << 14)
        lsb = lsb + (cfg.PSTAT_OTARI2X << 15)
        lsb = lsb + (cfg.PSTAT_OTAWI2X << 16)
        lsb = lsb + (cfg.PSTAT_S_SRE << 17)
        lsb = lsb + (cfg.PSTAT_S_CLSABR << 18)
        lsb = lsb + (cfg.PSTAT_S_OTAR << 19)
        lsb = lsb + (cfg.PSTAT_S_CLSABW << 20)
        lsb = lsb + (cfg.PSTAT_S_OTAW << 21)
        lsb = lsb + (cfg.PSTAT_S_CC << 22)
        lsb = lsb + (cfg.PSTAT_S_BIAS << 23)
        lsb = lsb + (ADC_MUX << 24)
        lsb = lsb + (self.binary_to_thermo(cfg.ADC_C2) << 26)
        lsb = lsb + (cfg.ADC_STARTUP_SEL << 30)

        msb = self.binary_to_thermo(cfg.ADC_OTA2)
        msb = msb + (self.binary_to_thermo(cfg.ADC_OTA1) << 2)
        msb = msb + (PM_EN << 4)
        msb = msb + (ION_EN << 5)
        msb = msb + (cfg.CGM_EXT << 6)
        msb = msb + (I_MUX_OUT << 7)
        print(f"Generated SPI config MSB: {hex(msb)}, LSB: {hex(lsb)}")
        return msb , lsb

    
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
        #expand to 32-bit
        code = code << 22
        return code

    def gen_ramp(self,vstart,vstop,vstep):
        '''
            vstart: starting voltage (mV)
            vstop: final voltage (mV)
            vstep: step voltage (mV)
        '''
        data = []
        steps = int((vstop-vstart)/vstep + 1)
        for i in range(steps):
            v = vstart + i * vstep
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        return data

    def gen_cv(self,vstart,v1,v2,vstep):
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
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        steps = int((v1-v2)/vstep + 1)
        for i in range(steps):
            v = v1 - i * vstep
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        return data

    def gen_dpv(self,vstart,vstop,vstep,vpulse):
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
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
            v = vstart + i * vstep + vpulse
            bin = self.analog_to_binary(v,cfg.VREF_MV)
            data.append(bin)
        return data
    
    def complete_to_multiple_of_16(self,lst):
        remainder = len(lst) % 4
        for i in range(4 - remainder):
            lst.append(lst[-1])  # repeat last item
        return lst
    
# -------------------------------------------------------------------------
# Quick bring-up test harness
# -------------------------------------------------------------------------
if __name__ == "__main__":
    bitfile = cfg.BITFILE

    fpga = OKTop(bitfile)

    print("Opening + configuring FPGA...")
    fpga.open_and_configure()

    print("Resetting system...")
    fpga.system_reset()

    fpga.set_modes(task_mode=0, dac_mode=0, adc_mode=0)
    print("Writing simple DAC/ADC configs...")
    
    wav = fpga.gen_ramp(vstart=2400, vstop=2560, vstep=10)
    print(f"Generated waveform with {len(wav)} samples.")

    fpga.config_dac(t1=100, t2=200, ts1=50, ts2=50, nsam=len(wav))
    
    fpga.config_adc(twake=100, tsample=2**20, nsam=1)

    
    msb, lsb = fpga.gen_config_code(I_MUX_OUT=0, ION_EN=0, PM_EN=0, ADC_MUX=0)
    print(f"Generated SPI config MSB: {hex(msb)}, LSB: {hex(lsb)}")

    fpga.write_spi_config_word40(msb_32=msb, lsb_32=lsb)
    
    fpga.trigger_spi_config()

    fpga.write_waveform_words(wav)

    cnt = fpga.read_spi_cnt()
    print(f"SPI triggered {cnt['raw']} times.")

    #print("Reading back SPI and ADC data...")
    spi_data_msb = fpga.read_spi_out_msb(4)
    spi_data_lsb = fpga.read_spi_out_lsb(4)

    print("SPI out (MSB) words:", [hex(x) for x in spi_data_msb])
    print("SPI out (LSB) words:", [hex(x) for x in spi_data_lsb])


    
    # ---------------------------------------------------------------
    #print("Triggering task...")
    fpga.trigger_task()
    data = fpga.task_watcher()

    with open("output.csv", "w") as f:
        for item in data:
            f.write(f"{item}\n")
