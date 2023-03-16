"""Constants for the Pylontech BMS component."""
from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "pylontech_console"

PLATFORMS = [Platform.SENSOR]

DEFAULT_NAME = "Pylontech BMS"
SCAN_INTERVAL = timedelta(seconds=30)

KEY_COORDINATOR = "coordinator"
