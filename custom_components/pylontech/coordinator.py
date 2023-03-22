"""Update coordinator for Pylontech BMS."""
from __future__ import annotations

import logging
from typing import Any

from .pylontech import InfoCommand, PylontechBMS, Sensor

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class PylontechUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Gather data for the energy device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        pylontech: PylontechBMS,
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
        self.pylontech = pylontech
        self.serial_nr = info.module_barcode.value
        self.device_info = _device(info)
        self.unit_device_infos = tuple(
            _unit_device(info, idx, bmu) for idx, bmu in enumerate(info.bmu_modules)
        )
        self.sensors: dict[str, Sensor] = {}
        self.unit_sensors: dict[str, Sensor] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the inverter."""
        try:
            await self.pylontech.connect()
            pwr = await self.pylontech.pwr()
            result = {k: v.value for k, v in vars(pwr).items()}
            unit = await self.pylontech.unit()
            for i, unt in enumerate(unit.values):
                result.update({f"{k}_bmu_{i}": v.value for k, v in vars(unt).items()})
            await self.pylontech.disconnect()
            return result
        except ValueError as ex:
            raise UpdateFailed(ex) from ex

    async def detect_sensors(self) -> None:
        """Retrieve all supported sensor names from BMS"""
        await self.pylontech.connect()
        pwr = await self.pylontech.pwr()
        self.sensors = vars(pwr)
        unit = await self.pylontech.unit()
        self.unit_sensors = vars(unit.values[0])
        await self.pylontech.disconnect()

    def sensor_value(self, sensor: str) -> Any:
        """Answer current value of the sensor."""
        return self.data.get(sensor)


def _device(info: InfoCommand) -> DeviceInfo:
    return DeviceInfo(
        # configuration_url=f"telnet://{pylontech.host}:{pylontech.port}",
        identifiers={(DOMAIN, info.module_barcode.value)},
        name="Pylontech BMS",
        model=info.device_name.value,
        manufacturer=info.manufacturer.value,
        sw_version=f"{info.main_sw_version.value} / {info.sw_version.value}",
    )


def _unit_device(info: InfoCommand, idx: int, bmu: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, bmu)},
        name=f"Pylontech BMU #{idx}",
        manufacturer=info.manufacturer.value,
        via_device=(DOMAIN, info.module_barcode.value),
    )
