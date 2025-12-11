import serial
import time

class CS580:
    """
    Simple Python wrapper for the Stanford Research Systems CS580
    Voltage Controlled Current Source.

    Remote interface: 9600 baud, 8N1, no flow control.
    """

    # Mapping of human-friendly gain names to CS580 tokens
    # See manual GAIN command table.
    GAIN_TOKENS = {
        1e-9:  "G1NA",
        10e-9: "G10NA",
        100e-9: "G100NA",
        1e-6:  "G1UA",
        10e-6: "G10UA",
        100e-6: "G100UA",
        1e-3:  "G1MA",
        10e-3: "G10MA",
        50e-3: "G50MA",
    }

    def __init__(self, port: str, timeout: float = 1.0):
        """
        port: e.g. 'COM3' on Windows or '/dev/ttyUSB0' on Linux.
        """
        self.ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
        )
        # Small delay after opening port
        time.sleep(0.1)

        # Optional: set token responses to text instead of numeric
        # so queries like GAIN? return 'G10UA' instead of '4'
        self.write("TOKN ON")

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    # --- low-level helpers ---

    def write(self, cmd: str):
        """
        Send a command (no response expected).
        CS580 parses commands terminated by CR or LF.
        """
        line = (cmd + "\n").encode("ascii")
        self.ser.write(line)

    def query(self, cmd: str) -> str:
        """
        Send a command and read back one line of response.
        """
        self.write(cmd)
        resp = self.ser.readline().decode("ascii", errors="ignore").strip()
        return resp

    # --- high-level commands ---

    def identify(self) -> str:
        """Return the *IDN? string."""
        return self.query("*IDN?")

    # Gain control ------------------------------------------------------

    def set_gain(self, human_gain: float):
        """
        Set voltage-to-current gain.

        Either:
          - gain_token: one of 'G1nA', 'G10nA', ..., 'G50mA'
          - human_gain: one of '1nA/V', '10nA/V', ..., '50mA/V'
        """
        
        gain_token = self.GAIN_TOKENS[human_gain]
        self.write(f"GAIN {gain_token}")

    def get_gain(self) -> str:
        """Return the current gain token (e.g. 'G10UA')."""
        return self.query("GAIN?")

    # Output enable -----------------------------------------------------

    def enable_output(self, on: bool = True):
        """
        Turn the current source output on/off.
        Equivalent to OUTPUT [Enable] button.
        """
        z = 1 if on else 0  # ON=1, OFF=0
        self.write(f"SOUT {z}")

    def is_output_on(self) -> bool:
        """Return True if output is enabled."""
        return self.query("SOUT?") in ("1", "ON")

    # Analog input (front-panel INPUT BNC) ------------------------------

    def enable_analog_input(self, on: bool = True):
        """
        Enable/disable using the analog input BNC as a control voltage.
        """
        z = "ON" if on else "OFF"  # ON=1, OFF=0
        self.write(f"INPT {z}")

    # DC current and compliance voltage --------------------------------

    def set_dc_current(self, current_amps: float):
        """
        Set the internal DC current (in amperes).
        Range is ±2 V * gain (e.g. GAIN=10 µA/V → ±20 µA). :contentReference[oaicite:1]{index=1}
        """
        if (current_amps < -1e-6) or (current_amps > 1e-6):
            amp_ua = current_amps * 1e6  # Convert to microamps
            self.write(f"CURR {amp_ua:.2f}E-6")
        else:
            amp_na = current_amps * 1e9  # Convert to nanoamps
            self.write(f"CURR {amp_na:.2f}E-9")

    def get_dc_current(self) -> float:
        """Query the DC current (in A)."""
        return float(self.query("CURR?"))

    def set_compliance_voltage(self, volts: float):
        """
        Set compliance voltage (0–50 V). Be careful: this is your
        max allowed load voltage before current limits. :contentReference[oaicite:2]{index=2}
        """
        if not (0.0 <= volts <= 50.0):
            raise ValueError("Compliance voltage must be between 0 and 50 V")
        self.write(f"VOLT {volts:.3f}")

    def get_compliance_voltage(self) -> float:
        """Query the compliance voltage (in V)."""
        return float(self.query("VOLT?"))

    # Shield / isolation / speed ---------------------------------------

    def set_shield(self, mode: str):
        """
        mode: 'GUARD' or 'RETURN'
        (Inner triax shield behavior)
        """
        mode = mode.upper()
        if mode not in ("GUARD", "RETURN"):
            raise ValueError("mode must be 'GUARD' or 'RETURN'")
        self.write(f"SHLD {mode}")

    def set_isolation(self, mode: str):
        """
        mode: 'GROUND' or 'FLOAT'
        (Current source return referenced to chassis or floating)
        """
        mode = mode.upper()
        if mode not in ("GROUND", "FLOAT"):
            raise ValueError("mode must be 'GROUND' or 'FLOAT'")
        self.write(f"ISOL {mode}")

    def set_speed(self, mode: str):
        """
        mode: 'FAST' or 'SLOW'
        (max bandwidth or extra 470 pF filter)
        """
        self.write(f"RESP {mode}")

    # Status / error helpers -------------------------------------------

    def get_overload(self) -> bool:
        """Return True if the CS580 reports overload (OVLD?)."""
        return self.query("OVLD?") == "1"

    def clear_status(self):
        """Clear status registers (*CLS)."""
        self.write("*CLS")

    def last_command_error(self) -> str:
        """Return last command error (LCME?)."""
        return self.query("LCME?")

    def last_execution_error(self) -> str:
        """Return last execution error (LEXE?)."""
        return self.query("LEXE?")
