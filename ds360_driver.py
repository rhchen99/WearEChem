import pyvisa as visa

class DS360:
    def __init__(self, gpib_address='GPIB0::8::INSTR'):
        self.rm = visa.ResourceManager()
        self.ds360 = self.rm.open_resource(gpib_address)
        self.ds360.write_termination = '\n'
        self.ds360.read_termination = '\r'

    def set_sine_waveform(self):
        """Configure the DS360 to output a sine waveform."""
        self.ds360.write('FUNC 0')

    def set_frequency(self, frequency_hz):
        """Set the frequency of the DS360 signal generator."""
        command = f'FREQ {frequency_hz}'
        self.ds360.write(command)

    def set_amplitude(self, amplitude_vr):
        """Set the amplitude of the DS360 signal generator."""
        command = f'AMPL{amplitude_vr}VR'
        self.ds360.write(command)
    
    def set_offset(self, offset):
        """Set the offset voltage of the DS360 signal generator."""
        command = f'OFFS{offset}'
        self.ds360.write(command)

    def output_on(self):
        """Turn on the output of the DS360 signal generator."""
        self.ds360.write('OUTE1')

    def output_off(self):
        """Turn off the output of the DS360 signal generator."""
        self.ds360.write('OUTE0')

    def close(self):
        """Close the connection to the DS360 signal generator."""
        self.ds360.close()
        self.rm.close()