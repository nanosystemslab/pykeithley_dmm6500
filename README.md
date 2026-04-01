# PyKeithley_DMM6500

[![PyPI](https://img.shields.io/pypi/v/pykeithley_dmm6500.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/pykeithley_dmm6500.svg)][pypi status]
[![Python Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fnanosystemslab%2Fpykeithley_dmm6500%2Fmain%2Fpyproject.toml)][pypi status]
[![License](https://img.shields.io/github/license/nanosystemslab/pykeithley_dmm6500)][license]

[![Read the Docs](https://img.shields.io/readthedocs/pykeithley-dmm6500/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/nanosystemslab/pykeithley_dmm6500/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/nanosystemslab/pykeithley_dmm6500/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/pykeithley_dmm6500/
[read the docs]: https://pykeithley-dmm6500.readthedocs.io/
[tests]: https://github.com/nanosystemslab/pykeithley_dmm6500/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/nanosystemslab/pykeithley_dmm6500
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

A Python library for controlling the Keithley DMM6500 digital multimeter over Ethernet (TCP/IP). Sends TSP (Test Script Processing) commands directly -- no VISA or NI drivers required.

## Features

- TCP/IP connection to DMM6500 on port 5025 (no VISA dependency)
- Context manager for automatic connection handling
- DC/AC voltage, DC/AC current, resistance (2-wire and 4-wire), temperature, capacitance, continuity, and diode measurement modes
- Full control over NPLC, range, input impedance, autozero, and measurement filters
- Trigger model control (initiate, abort, wait)
- Lua script upload to instrument
- Van der Pauw measurement configuration and sheet resistance calculation
- Command-line interface for quick measurements

## Requirements

- Python >= 3.10
- Keithley DMM6500 connected via Ethernet
- No additional dependencies (uses only Python standard library)

## Installation

You can install _PyKeithley_DMM6500_ via [pip] from [PyPI]:

```console
$ pip install pykeithley_dmm6500
```

Or install from source with Poetry:

```console
$ git clone https://github.com/nanosystemslab/pykeithley_dmm6500.git
$ cd pykeithley_dmm6500
$ poetry install
```

## Usage

### Python API

```python
from pykeithley_dmm6500 import DMM6500, Impedance

with DMM6500("169.254.11.31") as dmm:
    print(dmm.identify())

    # DC voltage measurement
    dmm.configure_dcv(range=1, nplc=10, impedance=Impedance.AUTO)
    voltage = dmm.measure()
    print(f"Voltage: {voltage:.6e} V")

    # Resistance measurement (2-wire)
    dmm.configure_resistance(range=10000, nplc=10)
    resistance = dmm.measure()
    print(f"Resistance: {resistance:.4f} ohm")

    # 4-wire resistance
    dmm.configure_resistance(range=10000, four_wire=True, nplc=10)
    resistance = dmm.measure()
    print(f"4W Resistance: {resistance:.4f} ohm")
```

### Van der Pauw Measurements

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

# With film thickness for resistivity
result = sheet_resistance_from_configs(
    v1, v2, v3, v4,
    current=100e-6,
    thickness_cm=100e-7,  # 100 nm
)
print(f"Resistivity:  {result.resistivity:.4e} ohm-cm")
```

### Verify Source Current

```python
with DMM6500("169.254.11.31") as dmm:
    # Put DMM in series with your current source to verify
    dmm.configure_dci_verify(expected_current=100e-6)
    actual_current = dmm.measure()
    print(f"Source current: {actual_current:.2e} A")
```

### Command-Line Interface

```console
# Identify instrument
$ pykeithley_dmm6500 169.254.11.31 identify

# Take a single DC voltage measurement
$ pykeithley_dmm6500 169.254.11.31 measure

# Take 10 readings with 1s delay, 100mV range
$ pykeithley_dmm6500 169.254.11.31 measure -n 10 -d 1.0 --range 0.1

# Reset instrument
$ pykeithley_dmm6500 169.254.11.31 reset
```

### Docker

A Dockerfile is included for development and testing:

```console
$ docker build -t pykeithley-dmm6500-dev .
$ docker run --rm pykeithley-dmm6500-dev                         # run tests
$ docker run --rm --network host pykeithley-dmm6500-dev poetry run python -c "
from pykeithley_dmm6500 import DMM6500
with DMM6500('169.254.11.31') as dmm:
    print(dmm.identify())
"
```

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [GPL 3.0 license][license],
_PyKeithley_DMM6500_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@nanosystemslab]'s [Nanosystems Lab Python Cookiecutter] template.

[@nanosystemslab]: https://github.com/nanosystemslab
[pypi]: https://pypi.org/
[nanosystems lab python cookiecutter]: https://github.com/nanosystemslab/cookiecutter-nanosystemslab
[file an issue]: https://github.com/nanosystemslab/pykeithley_dmm6500/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/nanosystemslab/pykeithley_dmm6500/blob/main/LICENSE
[contributor guide]: https://github.com/nanosystemslab/pykeithley_dmm6500/blob/main/CONTRIBUTING.md
[command-line reference]: https://pykeithley-dmm6500.readthedocs.io/en/latest/usage.html
