"""Update coordinator for Pylontech BMS."""
from __future__ import annotations

import logging
from typing import Any

from .pylontech import InfoCommand, PylontechConsole, Sensor

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_NAME, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class PylontechUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Gather data for the energy device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        pylontech: PylontechConsole,
        info: InfoCommand,
    ) -> None:
        """Initialize update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=SCAN_INTERVAL,
            update_method=self._async_update_data,
        )
        self.pylontech: PylontechConsole = pylontech
        self.serial_nr = info.module_barcode.value
        self.device_info = _device_info(pylontech, info)
        self.sensors: dict[str, Sensor] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the inverter."""
        try:
            await self.pylontech.connect()
            pwr = await self.pylontech.pwr()
            await self.pylontech.disconnect()
            return {k: v.value for k, v in vars(pwr).items()}
        except ValueError as ex:
            raise UpdateFailed(ex) from ex

    async def detect_sensors(self) -> dict[str, Sensor]:
        """Retrieve all supported sensor names from BMS"""
        await self.pylontech.connect()
        pwr = await self.pylontech.pwr()
        await self.pylontech.disconnect()
        self.sensors = vars(pwr)
        return self.sensors

    def sensor_value(self, sensor: str) -> Any:
        """Answer current value of the sensor."""
        return self.data.get(sensor)


def _device_info(pylontech: PylontechConsole, info: InfoCommand) -> DeviceInfo:
    return DeviceInfo(
        # configuration_url=f"telnet://{pylontech.host}:{pylontech.port}",
        identifiers={(DOMAIN, info.module_barcode.value)},
        name=DEFAULT_NAME,
        model=info.device_name.value,
        manufacturer=info.manufacturer.value,
        sw_version=f"{info.main_sw_version.value} / {info.sw_version.value}"
        #        hw_version
        #        via_device
    )
