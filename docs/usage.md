# Usage

## Installation

Install from PyPI:

```console
$ pip install pykeithley_dmm6500
```

Or install from source with Poetry:

```console
$ git clone https://github.com/nanosystemslab/pykeithley_dmm6500.git
$ cd pykeithley_dmm6500
$ poetry install
```

## Python API

### Connecting to the Instrument

The `DMM6500` class communicates over TCP/IP on port 5025 (no VISA required).
Use it as a context manager for automatic connection handling:

```python
from pykeithley_dmm6500 import DMM6500

with DMM6500("169.254.11.31") as dmm:
    print(dmm.identify())
```

Or manage the connection manually:

```python
dmm = DMM6500("169.254.11.31")
dmm.connect()
print(dmm.identify())
dmm.disconnect()
```

### DC Voltage Measurement

```python
from pykeithley_dmm6500 import DMM6500, Impedance

with DMM6500("169.254.11.31") as dmm:
    dmm.configure_dcv(range=1, nplc=10, impedance=Impedance.AUTO)
    voltage = dmm.measure()
    print(f"Voltage: {voltage:.6e} V")
```

### AC Voltage Measurement

```python
with DMM6500("169.254.11.31") as dmm:
    dmm.configure_acv(range=10)
    voltage = dmm.measure()
    print(f"AC Voltage: {voltage:.6e} V")
```

### Resistance Measurement

```python
with DMM6500("169.254.11.31") as dmm:
    # 2-wire resistance
    dmm.configure_resistance(range=10000, nplc=10)
    resistance = dmm.measure()
    print(f"Resistance: {resistance:.4f} ohm")

    # 4-wire resistance
    dmm.configure_resistance(range=10000, four_wire=True, nplc=10)
    resistance = dmm.measure()
    print(f"4W Resistance: {resistance:.4f} ohm")
```

### DC Current Measurement

```python
with DMM6500("169.254.11.31") as dmm:
    dmm.configure_dci(range=0.001, nplc=10)
    current = dmm.measure()
    print(f"Current: {current:.6e} A")
```

### Temperature Measurement

```python
with DMM6500("169.254.11.31") as dmm:
    dmm.configure_temperature()
    temp = dmm.measure()
    print(f"Temperature: {temp:.2f} C")
```

### Measurement Filters

Apply averaging filters to reduce noise:

```python
from pykeithley_dmm6500 import DMM6500, FilterType

with DMM6500("169.254.11.31") as dmm:
    dmm.configure_dcv(range=1, nplc=10)
    dmm.set_filter(enable=True, filter_type=FilterType.REPEAT_AVG, count=100)
    voltage = dmm.measure()
```

## Van der Pauw Measurements

The library includes optimized configuration for Van der Pauw sheet resistance
measurements and calculation utilities.

### Configure and Measure

```python
from pykeithley_dmm6500 import DMM6500, sheet_resistance_from_configs

with DMM6500("169.254.11.31") as dmm:
    # Configure for VdP voltage sensing
    # (DCV, auto-range, NPLC 10, >10 GOhm impedance, autozero, repeat filter)
    dmm.configure_van_der_pauw()

    # Measure all 4 configurations (swap probes between readings)
    v1 = dmm.measure()  # Config 1
    v2 = dmm.measure()  # Config 2 (reverse of 1)
    v3 = dmm.measure()  # Config 3
    v4 = dmm.measure()  # Config 4 (reverse of 3)

# Calculate sheet resistance
result = sheet_resistance_from_configs(v1, v2, v3, v4, current=100e-6)
print(f"R_horizontal: {result.r_horizontal:.2f} ohm")
print(f"R_vertical:   {result.r_vertical:.2f} ohm")
print(f"R_sheet:      {result.sheet_resistance:.2f} ohm/sq")
```

### Calculate Resistivity

Provide film thickness to compute resistivity:

```python
from pykeithley_dmm6500 import sheet_resistance_from_configs

result = sheet_resistance_from_configs(
    v1, v2, v3, v4,
    current=100e-6,
    thickness_cm=100e-7,  # 100 nm
)
print(f"Resistivity: {result.resistivity:.4e} ohm-cm")
```

### Verify Source Current

```python
with DMM6500("169.254.11.31") as dmm:
    dmm.configure_dci_verify(expected_current=100e-6)
    actual_current = dmm.measure()
    print(f"Source current: {actual_current:.2e} A")
```

## Command-Line Interface

```{eval-rst}
.. argparse::
    :module: pykeithley_dmm6500.__main__
    :func: create_parser
    :prog: pykeithley_dmm6500
```

### Examples

```console
$ pykeithley_dmm6500 169.254.11.31 identify

$ pykeithley_dmm6500 169.254.11.31 measure

$ pykeithley_dmm6500 169.254.11.31 measure -n 10 -d 1.0 --range 0.1

$ pykeithley_dmm6500 169.254.11.31 reset
```
