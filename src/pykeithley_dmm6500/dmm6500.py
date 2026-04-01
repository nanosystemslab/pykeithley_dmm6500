"""Keithley DMM6500 instrument driver over TCP/IP."""

import socket
from enum import Enum
from typing import Optional


class MeasureFunction(Enum):
    """DMM measurement functions."""

    DC_VOLTAGE = "dmm.FUNC_DC_VOLTAGE"
    AC_VOLTAGE = "dmm.FUNC_AC_VOLTAGE"
    DC_CURRENT = "dmm.FUNC_DC_CURRENT"
    AC_CURRENT = "dmm.FUNC_AC_CURRENT"
    RESISTANCE = "dmm.FUNC_RESISTANCE"
    FOUR_WIRE_RESISTANCE = "dmm.FUNC_4W_RESISTANCE"
    TEMPERATURE = "dmm.FUNC_TEMPERATURE"
    DIODE = "dmm.FUNC_DIODE"
    CAPACITANCE = "dmm.FUNC_CAPACITANCE"
    CONTINUITY = "dmm.FUNC_CONTINUITY"


class FilterType(Enum):
    """DMM measurement filter types."""

    REPEAT_AVG = "dmm.FILTER_REPEAT_AVG"
    MOVING_AVG = "dmm.FILTER_MOVING_AVG"


class Impedance(Enum):
    """DMM input impedance settings.

    AUTO selects >10 GOhm for ranges <= 100V (Hi-Z), 10 MOhm for higher.
    TEN_MEGAOHM forces 10 MOhm for all ranges.
    """

    AUTO = "dmm.IMPEDANCE_AUTO"
    TEN_MEGAOHM = "dmm.IMPEDANCE_10M"


class DMM6500:
    """Driver for Keithley DMM6500 digital multimeter.

    Args:
        ip_address: IP address of the instrument.
        port: TCP port number (default 5025).
        timeout: Socket timeout in seconds.
    """

    DEFAULT_PORT = 5025
    DEFAULT_TIMEOUT = 5.0

    def __init__(
        self,
        ip_address: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize DMM6500 connection parameters."""
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None

    def connect(self) -> None:
        """Open TCP connection to the instrument."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.timeout)
        self._socket.connect((self.ip_address, self.port))

    def disconnect(self) -> None:
        """Close the TCP connection."""
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "DMM6500":
        """Connect and return self for use as context manager."""
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        """Disconnect on context manager exit."""
        self.disconnect()

    def _check_connection(self) -> socket.socket:
        """Return the socket, raising if not connected."""
        if self._socket is None:
            raise ConnectionError("Not connected. Call connect() first.")
        return self._socket

    def send(self, command: str) -> None:
        """Send a TSP command to the instrument.

        Args:
            command: TSP command string.
        """
        sock = self._check_connection()
        if not command.endswith("\n"):
            command += "\n"
        sock.sendall(command.encode())

    def receive(self, buffer_size: int = 4096) -> str:
        """Read response from the instrument.

        Args:
            buffer_size: Maximum bytes to read.

        Returns:
            Response string with whitespace stripped.
        """
        sock = self._check_connection()
        return sock.recv(buffer_size).decode().strip()

    def query(self, command: str, buffer_size: int = 4096) -> str:
        """Send a command and return the response.

        Args:
            command: TSP command that produces output (use print()).
            buffer_size: Maximum bytes to read.

        Returns:
            Response string.
        """
        self.send(command)
        return self.receive(buffer_size)

    # ── Instrument control ──────────────────────────────────────────

    def reset(self) -> None:
        """Reset the instrument to factory defaults."""
        self.send("reset()")

    def identify(self) -> str:
        """Query the instrument identity string.

        Sends the ``*IDN?`` SCPI command.

        Returns:
            Instrument identification string.
        """
        return self.query("*IDN?")

    # ── Measurement configuration ───────────────────────────────────

    def set_function(self, func: MeasureFunction) -> None:
        """Set the measurement function.

        Args:
            func: Measurement function to select.
        """
        self.send(f"dmm.measure.func = {func.value}")

    def set_range(self, value: float) -> None:
        """Set the measurement range.

        Args:
            value: Range value in the unit of the active function.
        """
        self.send(f"dmm.measure.range = {value}")

    def set_auto_range(self, enable: bool = True) -> None:
        """Enable or disable auto-range.

        Args:
            enable: True to enable, False to disable.
        """
        state = "dmm.ON" if enable else "dmm.OFF"
        self.send(f"dmm.measure.autorange = {state}")

    def set_nplc(self, nplc: float) -> None:
        """Set the number of power line cycles for integration.

        Args:
            nplc: NPLC value (0.0005 to 15 for 60Hz, 0.0005 to 12 for 50Hz).
        """
        self.send(f"dmm.measure.nplc = {nplc}")

    def set_input_impedance(self, impedance: Impedance) -> None:
        """Set the input impedance mode.

        Args:
            impedance: Impedance setting.
        """
        self.send(f"dmm.measure.inputimpedance = {impedance.value}")

    def set_autozero(self, enable: bool = True) -> None:
        """Enable or disable autozero.

        Args:
            enable: True to enable, False to disable.
        """
        state = "dmm.ON" if enable else "dmm.OFF"
        self.send(f"dmm.measure.autozero.enable = {state}")

    # ── Filter configuration ────────────────────────────────────────

    def set_filter(
        self,
        enable: bool = True,
        filter_type: FilterType = FilterType.REPEAT_AVG,
        count: int = 10,
    ) -> None:
        """Configure the measurement filter.

        Args:
            enable: True to enable the filter.
            filter_type: Type of averaging filter.
            count: Number of readings to average.
        """
        self.send(f"dmm.measure.filter.type = {filter_type.value}")
        self.send(f"dmm.measure.filter.count = {count}")
        state = "dmm.ON" if enable else "dmm.OFF"
        self.send(f"dmm.measure.filter.enable = {state}")

    # ── Measurement ─────────────────────────────────────────────────

    def measure(self) -> float:
        """Take a single measurement with the current configuration.

        Returns:
            Measurement value as a float.
        """
        response = self.query("print(dmm.measure.read())")
        return float(response)

    # ── Convenience methods ─────────────────────────────────────────

    def configure_dcv(
        self,
        range: float = 10,
        nplc: float = 1,
        impedance: Impedance = Impedance.AUTO,
        autozero: bool = True,
    ) -> None:
        """Configure for DC voltage measurement.

        Args:
            range: Voltage range in volts.
            nplc: Number of power line cycles.
            impedance: Input impedance setting.
            autozero: Enable autozero.
        """
        self.set_function(MeasureFunction.DC_VOLTAGE)
        self.set_range(range)
        self.set_nplc(nplc)
        self.set_input_impedance(impedance)
        self.set_autozero(autozero)

    def configure_acv(self, range: float = 10) -> None:
        """Configure for AC voltage measurement.

        Args:
            range: Voltage range in volts.
        """
        self.set_function(MeasureFunction.AC_VOLTAGE)
        self.set_range(range)

    def configure_resistance(
        self, range: float = 1000, four_wire: bool = False, nplc: float = 1
    ) -> None:
        """Configure for resistance measurement.

        Args:
            range: Resistance range in ohms.
            four_wire: Use 4-wire measurement if True.
            nplc: Number of power line cycles.
        """
        func = (
            MeasureFunction.FOUR_WIRE_RESISTANCE
            if four_wire
            else MeasureFunction.RESISTANCE
        )
        self.set_function(func)
        self.set_range(range)
        self.set_nplc(nplc)

    def configure_temperature(self) -> None:
        """Configure for temperature measurement."""
        self.set_function(MeasureFunction.TEMPERATURE)

    def configure_dci(self, range: float = 1, nplc: float = 1) -> None:
        """Configure for DC current measurement.

        Args:
            range: Current range in amps.
            nplc: Number of power line cycles.
        """
        self.set_function(MeasureFunction.DC_CURRENT)
        self.set_range(range)
        self.set_nplc(nplc)

    # ── Application-specific configurations ────────────────────────

    def configure_van_der_pauw(
        self,
        voltage_range: float = 0.1,
        auto_range: bool = True,
        nplc: float = 10,
        filter_count: int = 10,
    ) -> None:
        """Configure for Van der Pauw voltage sensing.

        Sets up DC voltage measurement with high input impedance (>10 GOhm),
        autozero, and repeat averaging filter -- optimized for measuring
        small voltages across resistive thin-film samples.

        Args:
            voltage_range: Voltage range in volts (default 100mV).
                Ignored if auto_range is True.
            auto_range: Use auto-ranging (default True).
            nplc: Power line cycles for integration (default 10 for
                best 60Hz noise rejection).
            filter_count: Number of readings for repeat average filter
                (default 10).
        """
        self.set_function(MeasureFunction.DC_VOLTAGE)
        if auto_range:
            self.set_auto_range(True)
        else:
            self.set_range(voltage_range)
        self.set_nplc(nplc)
        self.set_input_impedance(Impedance.AUTO)
        self.set_autozero(True)
        self.set_filter(
            enable=True,
            filter_type=FilterType.REPEAT_AVG,
            count=filter_count,
        )

    def configure_dci_verify(
        self,
        expected_current: float = 100e-6,
        nplc: float = 10,
    ) -> None:
        """Configure DC current measurement for verifying source current.

        Useful for confirming the actual current from a bench supply
        before Van der Pauw measurements.

        Args:
            expected_current: Expected current in amps to set appropriate
                range (default 100uA).
            nplc: Power line cycles (default 10).
        """
        self.set_function(MeasureFunction.DC_CURRENT)
        # Select the smallest range that covers the expected current
        current_ranges = [10e-6, 100e-6, 1e-3, 10e-3, 100e-3, 1, 3]
        selected_range = 3.0
        for r in current_ranges:
            if r >= expected_current:
                selected_range = r
                break
        self.set_range(selected_range)
        self.set_nplc(nplc)
        self.set_autozero(True)

    # ── Trigger model ───────────────────────────────────────────────

    def trigger_initiate(self) -> None:
        """Start the trigger model."""
        self.send("trigger.model.initiate()")

    def trigger_abort(self) -> None:
        """Abort the trigger model."""
        self.send("trigger.model.abort()")

    def wait_complete(self, timeout_ms: int = 0) -> None:
        """Wait for all commands to complete.

        Args:
            timeout_ms: Timeout in milliseconds (0 = no timeout).
        """
        if timeout_ms > 0:
            self.send(f"waitcomplete({timeout_ms})")
        else:
            self.send("waitcomplete()")

    # ── Script management ───────────────────────────────────────────

    def load_script(self, name: str, script_path: str) -> None:
        """Upload and run a Lua script on the instrument.

        Args:
            name: Name for the script on the instrument.
            script_path: Local file path to the Lua script.
        """
        with open(script_path) as f:
            contents = f.read()
        self.send(f"if {name} ~= nil then script.delete({name!r}) end")
        self.send(f"loadscript {name}\n{contents}\nendscript")
        self.send(f"{name}()")

    def delete_script(self, name: str) -> None:
        """Delete a script from the instrument.

        Args:
            name: Name of the script to delete.
        """
        self.send(f"script.delete({name!r})")
