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
        self.pulse_ctrl_bit(cfg.CTRL_RST_BIT, pulse_time=0.0)
        print("Reset done.")

    def set_modes(self, task_mode: int, dac_mode: int, adc_mode: int):
        """
        Set the mode bits in WireIn 0x00.
        task_mode: 0/1
        dac_mode : 0/1
        adc_mode : 0/1
        """
        self.set_ctrl_bits(cfg.CTRL_TASK_MODE_BIT, bool(task_mode))
        self.set_ctrl_bits(cfg.CTRL_DAC_MODE_BIT,  bool(dac_mode))
        self.set_ctrl_bits(cfg.CTRL_ADC_MODE_BIT,  bool(adc_mode))

    # ---------------------------------------------------------------------
    # DAC / ADC configuration (WireIns)
    # ---------------------------------------------------------------------
    def config_dac(self, t1: int, t2: int, ts1: int, ts2: int, nsam: int):
        """Write DAC timing parameters into WireIns."""
        self.dev.SetWireInValue(cfg.EP_WI_DAC_T1,   t1 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_T2,   t2 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_TS1,  ts1 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_TS2,  ts2 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_DAC_NSAM, nsam & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print("DAC config written.")

    def config_adc(self, twake: int, tsample: int, nsam: int):
        """Write ADC timing parameters into WireIns."""
        self.dev.SetWireInValue(cfg.EP_WI_ADC_TWAKE,   twake & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_TSAMPLE, tsample & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_NSAM,    nsam & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print("ADC config written.")

    # ---------------------------------------------------------------------
    # ASIC register-based config (w09–w0E pack -> asic_word in HDL)
    # ---------------------------------------------------------------------
    def config_asic_from_constants(self):
        """
        Write PSTAT, I2X, CC, ADC, and CGM_EXT via WireIns 0x09–0x0E.

        Matches HDL packing:
            asic_word = {
                wi0C[4:0],      // ADC OTA settings
                wi0D[2:0],      // ADC startup sel
                wi0D[7:4],      // ADC C2
                wi09[6:0],      // PSTAT block enables
                wi0A[3:0],      // I2X switches
                wi0B[2:0],      // CC gain
                wi0B[11:7],     // CC sel (5 bits)
                wi0E[0],        // CGM_EXT
                8'd0
            }
        """
        # wi09: PSTAT enables (7 bits)
        w9 = 0
        if cfg.PSTAT_S_BIAS:   w9 |= 1 << 0
        if cfg.PSTAT_S_CC:     w9 |= 1 << 1
        if cfg.PSTAT_S_OTAW:   w9 |= 1 << 2
        if cfg.PSTAT_S_CLSABW: w9 |= 1 << 3
        if cfg.PSTAT_S_OTAR:   w9 |= 1 << 4
        if cfg.PSTAT_S_CLSABR: w9 |= 1 << 5
        if cfg.PSTAT_S_SRE:    w9 |= 1 << 6

        # wi0A: PSTAT I2X switches (4 bits)
        wA = 0
        if cfg.PSTAT_OTAWI2X:   wA |= 1 << 0
        if cfg.PSTAT_OTARI2X:   wA |= 1 << 1
        if cfg.PSTAT_CLSABWI2X: wA |= 1 << 2
        if cfg.PSTAT_CLSABRI2X: wA |= 1 << 3

        # wi0B: CC gain (bits 2:0) + CC sel (bits 11:7)
        wB = 0
        wB |= (cfg.CC_GAIN & 0x7)          # bits [2:0]
        wB |= (cfg.CC_SEL & 0x1F) << 7     # bits [11:7]

        # wi0C: ADC OTA settings. You can change packing later if needed.
        # Here: lower 2 bits = OTA1, next 2 bits = OTA2.
        wC = 0
        wC |= (cfg.ADC_OTA1 & 0x3) << 0
        wC |= (cfg.ADC_OTA2 & 0x3) << 2
        # wC[4] left as 0 for now.

        # wi0D: ADC startup sel (2:0) + C2 (7:4)
        wD = 0
        wD |= (cfg.ADC_STARTUP_SEL & 0x7)      # bits [2:0]
        wD |= (cfg.ADC_C2 & 0xF) << 4          # bits [7:4]

        # wi0E: CGM_EXT in bit0
        wE = (cfg.CGM_EXT & 0x1)

        self.dev.SetWireInValue(cfg.EP_WI_PSTAT_EN,  w9 & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_PSTAT_I2X, wA & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_CC_CFG,    wB & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_OTA,   wC & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_ADC_MISC,  wD & 0xFFFFFFFF)
        self.dev.SetWireInValue(cfg.EP_WI_CGM_EXT,   wE & 0xFFFFFFFF)
        self.dev.UpdateWireIns()
        print("ASIC config (PSTAT/CC/ADC/CGM) written to WireIns 0x09–0x0E.")

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
        """
        Send a 40-bit config 'word' to the SPI config FIFO via PipeIn 0x80.

        HDL side:
          - First 32-bit word -> cfg_msb_reg
          - Second 32-bit word -> cfg_lsb_reg
          - Then spi_config_wr pulses for one cycle

        In WETOP:
          use_host = spi_config_wr;
          spi_word = use_host ? {msb[7:0], lsb} : asic_word;
        """
        payload = self._u32_to_bytes_le(msb_32) + self._u32_to_bytes_le(lsb_32)
        buf = bytearray(payload)
        self.dev.WriteToPipeIn(cfg.EP_PI_CONFIG, buf)
        print("SPI config 40-bit word sent (MSB,LSB) via PipeIn 0x80.")

    def trigger_spi_config(self):
        """
        Kick off the SPI/config FSM via TriggerIn 0x40, bit0.
        If you previously wrote to EP_PI_CONFIG, it uses host 40-bit word.
        If not, it uses the ASIC word built from WireIns 0x09–0x0E.
        """
        self.dev.ActivateTriggerIn(cfg.EP_TI_MAIN, cfg.TRIG_CONFIG_BIT)
        print("SPI/config trigger sent (TRIG_CONFIG_BIT).")

    # ---------------------------------------------------------------------
    # Waveform FIFO
    # ---------------------------------------------------------------------
    def write_waveform_words(self, words32):
        """
        Write a list of 32-bit integers into the waveform FIFO via PipeIn 0x81.
        """
        payload = b"".join(self._u32_to_bytes_le(w) for w in words32)
        if not payload:
            return
        buf = bytearray(payload)
        self.dev.WriteToPipeIn(cfg.EP_PI_WAVEFORM, buf)
        print(f"Wrote {len(words32)} words to waveform FIFO (0x81).")

    # ---------------------------------------------------------------------
    # Task trigger + completion
    # ---------------------------------------------------------------------
    def trigger_task(self):
        """Kick off the 'task' FSM via TriggerIn 0x40, bit1."""
        self.dev.ActivateTriggerIn(cfg.EP_TI_MAIN, cfg.TRIG_TASK_BIT)
        print("Task trigger sent (TRIG_TASK_BIT).")

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
        got = self.dev.ReadFromPipeOut(cfg.EP_PO_SPI_OUT, buf)
        if got != n_bytes:
            print(f"Warning: expected {n_bytes} bytes, got {got}.")
        raw = bytes(buf[:got])
        words = [int.from_bytes(raw[i:i+4], "little") for i in range(0, len(raw), 4)]
        return words

    def read_adc_out(self, n_words: int):
        """
        Read n_words of ADC output data from PipeOut 0xA1.
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

    print("Setting modes: task=1, dac=1, adc=1")
    fpga.set_modes(task_mode=1, dac_mode=1, adc_mode=1)

    print("Writing simple DAC/ADC configs...")
    fpga.config_dac(t1=100, t2=200, ts1=50, ts2=50, nsam=16)
    fpga.config_adc(twake=10, tsample=20, nsam=16)

    # ---------------------------------------------------------------
    # ASIC-wire-based SPI config path (uses wi09–wi0E -> asic_word)
    # ---------------------------------------------------------------
    print("Writing ASIC config via WireIns 0x09–0x0E...")
    fpga.config_asic_from_constants()
    print("Triggering SPI using ASIC config word...")
    fpga.trigger_spi_config()

    # ---------------------------------------------------------------
    # OPTIONAL: host 40-bit SPI config path (manual override)
    # Uncomment if you want to test the host-based packing:
    #
    # print("Sending dummy SPI config word from host...")
    # msb = 0x00000001
    # lsb = 0x000000AA
    # fpga.write_spi_config_word40(msb_32=msb, lsb_32=lsb)
    # fpga.trigger_spi_config()
    # ---------------------------------------------------------------

    print("Sending dummy waveform (ramp)...")
    ramp = list(range(16))
    fpga.write_waveform_words(ramp)

    print("Triggering task...")
    fpga.trigger_task()
    fpga.wait_for_task_done(timeout_s=0.5)

    print("Reading back SPI and ADC data...")
    spi_data = fpga.read_spi_out_msb(4)
    adc_data = fpga.read_adc_out(4)
    status = fpga.read_status()

    print("SPI out (MSB) words:", [hex(x) for x in spi_data])
    print("ADC out words:", [hex(x) for x in adc_data])
    print("Status:", status)
