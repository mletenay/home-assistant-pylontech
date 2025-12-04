"""Unit tests for Pylontech BMS sensor classes."""

import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock homeassistant modules before importing
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.exceptions"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.config_validation"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.helpers.entity"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()

# Add parent directory to path to import custom_components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can safely import from custom_components
from custom_components.pylontech.pylontech import (
    Text,
    Integer,
    Voltage,
    Current,
    Temp,
    Percent,
    ChargeAh,
    ChargeWh,
    Boolean,
)


class TestSensorClasses(unittest.TestCase):
    """Test basic sensor classes."""

    def test_text_sensor(self):
        """Test Text sensor initialization and set."""
        sensor = Text("Test Label")
        self.assertEqual(sensor.name, "Test Label")
        self.assertEqual(sensor.unit, " ")
        self.assertIsNone(sensor.value)

        sensor.set("test value")
        self.assertEqual(sensor.value, "test value")

    def test_text_sensor_fetch(self):
        """Test Text sensor fetch method."""
        sensor = Text("Test Label")
        lines = ["Test Label: some value", "other line"]
        sensor.fetch(lines)
        self.assertEqual(sensor.value, " some value")
        self.assertEqual(len(lines), 1)  # One line should be removed

    def test_integer_sensor(self):
        """Test Integer sensor."""
        sensor = Integer("Count")
        sensor.set("42")
        self.assertEqual(sensor.value, 42)
        self.assertIsInstance(sensor.value, int)

    def test_integer_sensor_fetch(self):
        """Test Integer sensor fetch."""
        sensor = Integer("Count")
        lines = ["Count: 99", "other"]
        sensor.fetch(lines)
        self.assertEqual(sensor.value, 99)
        self.assertEqual(len(lines), 1)

    def test_voltage_sensor(self):
        """Test Voltage sensor."""
        sensor = Voltage("Battery Voltage")
        sensor.set("48000")
        self.assertEqual(sensor.value, 48.0)
        self.assertEqual(sensor.unit, "V")

    def test_voltage_sensor_custom_divider(self):
        """Test Voltage sensor with custom divider."""
        sensor = Voltage("Cell Voltage")
        sensor.set("3300", divider=1000)
        self.assertEqual(sensor.value, 3.3)

    def test_current_sensor(self):
        """Test Current sensor."""
        sensor = Current("Battery Current")
        sensor.set("25000")
        self.assertEqual(sensor.value, 25.0)
        self.assertEqual(sensor.unit, "A")

    def test_current_sensor_with_ma(self):
        """Test Current sensor with mA suffix."""
        sensor = Current("Battery Current")
        sensor.set("25000mA")
        self.assertEqual(sensor.value, 25.0)

    def test_temp_sensor(self):
        """Test Temperature sensor."""
        sensor = Temp("Temperature")
        sensor.set("25000")
        self.assertEqual(sensor.value, 25.0)
        self.assertEqual(sensor.unit, "C")

    def test_percent_sensor(self):
        """Test Percent sensor."""
        sensor = Percent("Charge Level")
        sensor.set("68%")
        self.assertEqual(sensor.value, 68)
        self.assertEqual(sensor.unit, "%")

    def test_charge_ah_sensor(self):
        """Test Charge Ah sensor."""
        sensor = ChargeAh("Charge")
        sensor.set("33811")
        self.assertAlmostEqual(sensor.value, 33.811)
        self.assertEqual(sensor.unit, "Ah")

    def test_charge_wh_sensor(self):
        """Test Charge Wh sensor."""
        sensor = ChargeWh("Energy")
        sensor.set("1000000")
        self.assertEqual(sensor.value, 1000000)
        self.assertEqual(sensor.unit, "Wh")

    def test_boolean_sensor(self):
        """Test Boolean sensor."""
        sensor = Boolean("Active")
        sensor.set("Y")
        self.assertTrue(sensor.value)

        sensor.set("N")
        self.assertFalse(sensor.value)

    def test_sensor_string_representation(self):
        """Test __str__ method of sensors."""
        sensor = Text("Label")
        sensor.set("value")
        str_repr = str(sensor)
        self.assertIn("Label", str_repr)
        self.assertIn("value", str_repr)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_text_sensor_empty_string(self):
        """Test Text sensor with empty string."""
        sensor = Text("Label")
        sensor.set("")
        self.assertEqual(sensor.value, "")

    def test_percent_sensor_boundary(self):
        """Test Percent sensor with boundary values."""
        sensor = Percent("Level")
        sensor.set("0%")
        self.assertEqual(sensor.value, 0)

        sensor.set("100%")
        self.assertEqual(sensor.value, 100)

    def test_voltage_sensor_zero(self):
        """Test Voltage sensor with zero value."""
        sensor = Voltage("Voltage")
        sensor.set("0")
        self.assertEqual(sensor.value, 0.0)

    def test_current_sensor_negative(self):
        """Test Current sensor with negative value."""
        sensor = Current("Current")
        sensor.set("-1000")
        self.assertEqual(sensor.value, -1.0)

    def test_temp_sensor_high_value(self):
        """Test Temperature sensor with high value."""
        sensor = Temp("Temperature")
        sensor.set("50000")
        self.assertEqual(sensor.value, 50.0)


if __name__ == "__main__":
    unittest.main()
