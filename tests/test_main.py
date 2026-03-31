"""Test cases for the pykeithley_dmm6500 package."""

import math
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from pykeithley_dmm6500 import DMM6500
from pykeithley_dmm6500 import FilterType
from pykeithley_dmm6500 import Impedance
from pykeithley_dmm6500 import MeasureFunction
from pykeithley_dmm6500 import sheet_resistance
from pykeithley_dmm6500 import sheet_resistance_from_configs


@pytest.fixture
def mock_socket():
    """Create a mock socket for testing without hardware."""
    with patch("pykeithley_dmm6500.dmm6500.socket.socket") as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock_cls.return_value = mock_sock
        yield mock_sock


@pytest.fixture
def dmm(mock_socket):
    """Create a connected DMM6500 instance with mocked socket."""
    instrument = DMM6500("192.168.1.1")
    instrument.connect()
    return instrument


class TestConnection:
    """Test connection management."""

    def test_connect(self, mock_socket):
        dmm = DMM6500("192.168.1.1", port=5025)
        dmm.connect()
        mock_socket.settimeout.assert_called_once_with(5.0)
        mock_socket.connect.assert_called_once_with(("192.168.1.1", 5025))

    def test_disconnect(self, dmm, mock_socket):
        dmm.disconnect()
        mock_socket.close.assert_called_once()
        assert dmm._socket is None

    def test_context_manager(self, mock_socket):
        with DMM6500("192.168.1.1") as dmm:
            mock_socket.connect.assert_called_once()
        mock_socket.close.assert_called_once()

    def test_send_without_connection_raises(self):
        dmm = DMM6500("192.168.1.1")
        with pytest.raises(ConnectionError):
            dmm.send("reset()")


class TestSendReceive:
    """Test command send/receive."""

    def test_send_appends_newline(self, dmm, mock_socket):
        dmm.send("reset()")
        mock_socket.sendall.assert_called_with(b"reset()\n")

    def test_send_no_double_newline(self, dmm, mock_socket):
        dmm.send("reset()\n")
        mock_socket.sendall.assert_called_with(b"reset()\n")

    def test_query(self, dmm, mock_socket):
        mock_socket.recv.return_value = b"1.23456e-03\n"
        result = dmm.query("print(dmm.measure.read())")
        assert result == "1.23456e-03"


class TestConfiguration:
    """Test measurement configuration."""

    def test_set_function(self, dmm, mock_socket):
        dmm.set_function(MeasureFunction.DC_VOLTAGE)
        mock_socket.sendall.assert_called_with(
            b"dmm.measure.func = dmm.FUNC_DC_VOLTAGE\n"
        )

    def test_set_range(self, dmm, mock_socket):
        dmm.set_range(10)
        mock_socket.sendall.assert_called_with(b"dmm.measure.range = 10\n")

    def test_set_nplc(self, dmm, mock_socket):
        dmm.set_nplc(10)
        mock_socket.sendall.assert_called_with(b"dmm.measure.nplc = 10\n")

    def test_set_input_impedance(self, dmm, mock_socket):
        dmm.set_input_impedance(Impedance.AUTO)
        mock_socket.sendall.assert_called_with(
            b"dmm.measure.inputimpedance = dmm.IMPEDANCE_AUTO\n"
        )

    def test_set_autozero(self, dmm, mock_socket):
        dmm.set_autozero(True)
        mock_socket.sendall.assert_called_with(
            b"dmm.measure.autozero.enable = dmm.ON\n"
        )

    def test_set_filter(self, dmm, mock_socket):
        dmm.set_filter(enable=True, filter_type=FilterType.REPEAT_AVG, count=100)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"dmm.measure.filter.type = dmm.FILTER_REPEAT_AVG\n" in calls
        assert b"dmm.measure.filter.count = 100\n" in calls
        assert b"dmm.measure.filter.enable = dmm.ON\n" in calls


class TestMeasurement:
    """Test measurement methods."""

    def test_measure(self, dmm, mock_socket):
        mock_socket.recv.return_value = b"1.00234e+00\n"
        value = dmm.measure()
        assert isinstance(value, float)
        assert value == pytest.approx(1.00234)

    def test_configure_dcv(self, dmm, mock_socket):
        dmm.configure_dcv(range=1, nplc=10, impedance=Impedance.AUTO, autozero=True)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"dmm.measure.func = dmm.FUNC_DC_VOLTAGE\n" in calls
        assert b"dmm.measure.range = 1\n" in calls
        assert b"dmm.measure.nplc = 10\n" in calls

    def test_configure_resistance_4wire(self, dmm, mock_socket):
        dmm.configure_resistance(range=1000, four_wire=True)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"dmm.measure.func = dmm.FUNC_4W_RESISTANCE\n" in calls


class TestTrigger:
    """Test trigger model control."""

    def test_trigger_initiate(self, dmm, mock_socket):
        dmm.trigger_initiate()
        mock_socket.sendall.assert_called_with(b"trigger.model.initiate()\n")

    def test_trigger_abort(self, dmm, mock_socket):
        dmm.trigger_abort()
        mock_socket.sendall.assert_called_with(b"trigger.model.abort()\n")

    def test_wait_complete(self, dmm, mock_socket):
        dmm.wait_complete()
        mock_socket.sendall.assert_called_with(b"waitcomplete()\n")


class TestReset:
    """Test instrument control."""

    def test_reset(self, dmm, mock_socket):
        dmm.reset()
        mock_socket.sendall.assert_called_with(b"reset()\n")

    def test_identify(self, dmm, mock_socket):
        mock_socket.recv.return_value = (
            b"KEITHLEY INSTRUMENTS,MODEL DMM6500,04560740,1.7.12b\n"
        )
        idn = dmm.identify()
        assert "DMM6500" in idn


class TestVanDerPauw:
    """Test Van der Pauw configuration and calculations."""

    def test_configure_van_der_pauw_defaults(self, dmm, mock_socket):
        dmm.configure_van_der_pauw()
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"dmm.measure.func = dmm.FUNC_DC_VOLTAGE\n" in calls
        assert b"dmm.measure.autorange = dmm.ON\n" in calls
        assert b"dmm.measure.nplc = 10\n" in calls
        assert b"dmm.measure.inputimpedance = dmm.IMPEDANCE_AUTO\n" in calls
        assert b"dmm.measure.autozero.enable = dmm.ON\n" in calls
        assert b"dmm.measure.filter.type = dmm.FILTER_REPEAT_AVG\n" in calls
        assert b"dmm.measure.filter.count = 10\n" in calls
        assert b"dmm.measure.filter.enable = dmm.ON\n" in calls

    def test_configure_van_der_pauw_manual_range(self, dmm, mock_socket):
        dmm.configure_van_der_pauw(auto_range=False, voltage_range=0.1)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"dmm.measure.range = 0.1\n" in calls
        assert b"dmm.measure.autorange = dmm.ON\n" not in calls

    def test_configure_dci_verify(self, dmm, mock_socket):
        dmm.configure_dci_verify(expected_current=100e-6)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"dmm.measure.func = dmm.FUNC_DC_CURRENT\n" in calls
        assert b"dmm.measure.range = 0.0001\n" in calls
        assert b"dmm.measure.nplc = 10\n" in calls

    def test_configure_dci_verify_selects_correct_range(self, dmm, mock_socket):
        dmm.configure_dci_verify(expected_current=5e-6)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"dmm.measure.range = 1e-05\n" in calls

    def test_sheet_resistance_symmetric(self):
        # For a symmetric sample, R_h == R_v
        current = 100e-6
        voltage = 5e-3  # 5mV
        result = sheet_resistance(voltage, voltage, current)
        expected_rs = (math.pi / math.log(2)) * (voltage / current)
        assert result.sheet_resistance == pytest.approx(expected_rs)
        assert result.r_horizontal == pytest.approx(voltage / current)
        assert result.r_vertical == pytest.approx(voltage / current)
        assert result.resistivity is None

    def test_sheet_resistance_with_thickness(self):
        current = 100e-6
        voltage = 5e-3
        thickness = 100e-7  # 100nm in cm
        result = sheet_resistance(voltage, voltage, current, thickness_cm=thickness)
        assert result.resistivity is not None
        assert result.resistivity == pytest.approx(
            result.sheet_resistance * thickness
        )

    def test_sheet_resistance_from_configs(self):
        current = 100e-6
        # Forward/reverse pairs with slight offset
        v1, v2 = 5.1e-3, 4.9e-3   # horizontal pair
        v3, v4 = 5.2e-3, 4.8e-3   # vertical pair
        result = sheet_resistance_from_configs(v1, v2, v3, v4, current)
        # Averages should be 5.0mV for both
        assert result.r_horizontal == pytest.approx(50.0)  # 5mV / 100uA
        assert result.r_vertical == pytest.approx(50.0)
        expected_rs = (math.pi / math.log(2)) * 50.0
        assert result.sheet_resistance == pytest.approx(expected_rs)


class TestScriptManagement:
    """Test Lua script upload."""

    def test_load_script(self, dmm, mock_socket, tmp_path):
        script = tmp_path / "test.lua"
        script.write_text('print("hello")')
        dmm.load_script("myscript", str(script))
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert any(b"loadscript myscript" in c for c in calls)
        assert any(b"myscript()" in c for c in calls)
