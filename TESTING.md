# Pylontech BMS Unit Test Suite

## Overview

Comprehensive unit tests for the Pylontech BMS command parsing module (`pylontech.py`). The test suite provides 58 tests across 2 test files covering all command parsing classes and sensor types.

## Running the Tests

```bash
# Run all tests with verbose output
python3 -m unittest discover tests -v

# Run command parsing tests
python3 -m unittest tests.test_pylontech_commands -v

# Run sensor class tests
python3 -m unittest tests.test_sensor_classes -v

# Run specific test class
python3 -m unittest tests.test_pylontech_commands.TestPwrCommand -v

# Run specific test
python3 -m unittest tests.test_pylontech_commands.TestPwrCommand.test_pwr_command_voltage -v
```

## Test Coverage

Tests are organized into two files:

### `test_pylontech_commands.py` - Command Parsing Tests (39 tests)

#### 1. **BatCommand Tests** (7 tests)

Tests for battery cell command parsing:

- Initialization and attribute presence
- Temperature, current, state parsing
- Cell values and string representation
- Multi-format support (B50, B52.12.0)

#### 2. **BatValues Tests** (4 tests)

Individual battery cell parsing:

- Voltage, current, temperature, state parsing
- Support for Wh-based headers
- String representation

#### 3. **PwrCommand Tests** (8 tests)

Power/summary command parsing:

- Voltage, current, temperature parsing
- Cell and unit extremes (min/max)
- State attributes
- Multi-format support (B50, B52.12.0)

#### 4. **UnitCommand Tests** (9 tests)

Battery module/unit command parsing:

- Unit initialization and values
- Position tracking
- Voltage, current, temperature, charge parsing
- Multi-format support (B50, B52.12.0)

#### 5. **InfoCommand Tests** (12 tests)

Device information command parsing:

- Device address, manufacturer, device name
- Version information (board, hardware, software)
- Specifications and cell numbers
- Max currents and barcodes
- BMU module tracking
- String representation

### `test_sensor_classes.py` - Sensor Tests (19 tests)

#### 6. **Sensor Classes Tests** (14 tests)

Basic sensor types and their parsing:

- Text, Integer, Voltage, Current, Temperature sensors
- Percent, ChargeAh, ChargeWh, Boolean sensors
- Sensor fetch methods and string representations
- Custom dividers for voltage sensors

#### 7. **Edge Cases Tests** (5 tests)

Boundary conditions and edge cases:

- Empty strings, zero values, negative values
- Boundary percent values (0%, 100%)
- High temperature values

## Test Results

```
Command tests:  Ran 39 tests in 0.005s - OK
Sensor tests:   Ran 19 tests in 0.000s - OK
Total:          Ran 58 tests in 0.005s - OK
```

- **Passed**: 58 tests
- **Skipped**: 0 tests
- **Failed**: 0 tests

## Key Features

### Mock Home Assistant Integration

The tests use mocking to run without Home Assistant installation:

```python
sys.modules['homeassistant'] = MagicMock()
sys.modules['homeassistant.helpers.entity'] = MagicMock()
# ... more mocks
```

### Test Data

- Uses real sample data from multiple BMS firmware versions:
  - `tests/sample/B50/` - B50 format samples
  - `tests/sample/B52.12.0/` - B52.12.0 format samples
- Each directory contains:
  - `info.txt` - Device information
  - `bat.txt` - Battery cell data
  - `pwr.txt` - Power summary
  - `unit.txt` - Unit/module data
- Tests iterate over all available sample files for comprehensive coverage

### Error Handling

Tests gracefully handle:

- Missing sample data files (graceful skip)
- Malformed rows in sample data (exception handling with skip)
- Format variations between BMS versions (path-based conditional assertions)
- Data parsing edge cases (sanity checks only for sample files)

## Test Classes and Methods

### Sensor Class Methods

See `test_sensor_classes.py` for full list. Main test categories:

- Basic sensor types (Text, Integer, Voltage, Current, Temperature)
- Advanced sensors (Percent, ChargeAh, ChargeWh, Boolean)
- Sensor features (Fetch methods, string representations, custom dividers)
- Edge cases (Empty strings, boundary values, negative values, zero values)

### TestBatCommand (Sample Files Only)

All tests iterate over available sample files (B50, B52.12.0):

- `test_bat_command_initialization()` - Command creation with graceful skip on error
- `test_bat_command_parsing_attributes()` - Attribute presence check
- `test_bat_command_temperature()` - Average temperature if available
- `test_bat_command_currents()` - Charge/discharge currents if available
- `test_bat_command_state()` - Battery state presence
- `test_bat_command_cell_values()` - Cell data if present
- `test_bat_command_string_representation()` - String output

### TestBatValues

- `test_bat_values_initialization()` - Cell value parsing
- `test_bat_values_attributes()` - Required attributes
- `test_bat_values_with_wh_header()` - Wh-based format
- `test_bat_values_string_representation()` - String output

### TestPwrCommand (Multi-Format Support)

Iterates over B50 and B52.12.0 sample files with format-aware assertions:

- `test_pwr_command_initialization()` - Command creation
- `test_pwr_command_parsing_attributes()` - Attribute presence
- `test_pwr_command_voltage()` - Voltage parsing
- `test_pwr_command_current()` - Current parsing
- `test_pwr_command_temperature()` - Temperature parsing
- `test_pwr_command_cell_voltages()` - Min/max cell voltages
- `test_pwr_command_states()` - State attributes
- `test_pwr_command_string_representation()` - String output

### TestUnitCommand (Sample Files)

Tests unit/module command parsing from B50 and B52.12.0 samples:

- `test_unit_command_initialization()` - Command creation
- `test_unit_command_has_units()` - Unit count validation
- `test_unit_values_attributes()` - Required attributes check
- `test_unit_values_position()` - Unit positioning
- `test_unit_values_voltage()` - Voltage parsing
- `test_unit_values_temperature()` - Temperature parsing
- `test_unit_values_charge_ah()` - Charge parsing
- `test_unit_command_string_representation()` - String output

### TestInfoCommand

- `test_info_command_initialization()` - Command creation
- `test_info_command_device_address()` - Address parsing
- `test_info_command_manufacturer()` - Manufacturer name
- `test_info_command_device_name()` - Device name
- `test_info_command_versions()` - Version attributes
- `test_info_command_main_sw_version()` - Software version
- `test_info_command_spec()` - Specification field
- `test_info_command_cell_number()` - Cell count
- `test_info_command_max_currents()` - Max discharge/charge
- `test_info_command_barcodes()` - Barcode fields
- `test_info_command_bmu_modules()` - BMU module tracking
- `test_info_command_string_representation()` - String output

## File Organization

**test_pylontech_commands.py** (550 lines)

- Command parsing tests
- Multi-file dataset loading for B50 and B52.12.0 formats
- Exception handling for malformed sample data

**test_sensor_classes.py** (155 lines)

- Sensor class tests
- Edge case boundary condition tests
- Clean mock setup for Home Assistant modules

## Dependencies

The tests require no external packages beyond Python 3 standard library:

- `unittest` - Test framework
- `unittest.mock` - Mocking for Home Assistant modules
- Sample data files in `tests/sample/` directory
- No Home Assistant installation needed (fully mocked)
- Python 3.7+ required

## Notes

- Tests use mocking to avoid Home Assistant dependency
- All tests use real sample data files (no synthetic data generation)
- Malformed sample data is gracefully skipped with exception handling
- Multi-file dataset support: tests automatically discover and iterate over available sample files
- Tests are designed to be run from the repository root directory
- Compatible with Python 3.7+
