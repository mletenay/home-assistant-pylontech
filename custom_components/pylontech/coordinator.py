"""Update coordinator for Pylontech BMS."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .pylontech import InfoCommand, PylontechBMS, Sensor

_LOGGER = logging.getLogger(__name__)


class PylontechUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Gather data for the energy device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        pylontech: PylontechBMS,
        info: InfoCommand,
        bmu_serials: tuple[str],
    ) -> None:
        """Initialize update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=SCAN_INTERVAL,
            update_method=self._async_update_data,
        )
        self.pylontech: PylontechBMS = pylontech
        self.serial_nr: str = info.module_barcode.value
        self.device_info: DeviceInfo = _device(info)
        self.unit_device_infos: tuple[DeviceInfo] = tuple(
            _unit_device(info, idx, bmu) for idx, bmu in enumerate(info.bmu_modules)
        )
        self.sensors: dict[str, Sensor] = {}
        self.unit_sensors: dict[str, Sensor] = {}
        self.bat_sensors: dict[str, Sensor] = {}

        # Get stable unit position mapping (in case unit are physically re-ordered)
        known_positions: dict[str, int] = {b: i for i, b in enumerate(bmu_serials)}
        serials = len(bmu_serials)
        for d in self.unit_device_infos:
            if d["serial_number"] not in bmu_serials:
                known_positions[d["serial_number"]] = serials
                serials = serials + 1
        self._unit_positions: dict[int, int] = {
            i: known_positions[d["serial_number"]]
            for i, d in enumerate(self.unit_device_infos)
        }
        _LOGGER.debug("Created stable unit number mapping %s", self._unit_positions)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the inverter."""
        try:
            await self.pylontech.connect()
            pwr = await self.pylontech.pwr()
            result = {k: v.value for k, v in pwr.get_sensors().items()}
            unit = await self.pylontech.unit()
            for i, unt in enumerate(unit.values):
                bmu = self.get_unit_number(i)
                _LOGGER.debug("Updating BMU #%d sensors", bmu)
                result.update(
                    {f"{k}_bmu_{bmu}": v.value for k, v in unt.get_sensors().items()}
                )
            bat = await self.pylontech.bat()
            for i, bt in enumerate(bat.values):
                bmu = self.get_unit_number(bt.unit)
                cell = i % 15
                _LOGGER.debug("Updating cell #%d (bmu #%d) sensors", cell, bmu)
                result.update(
                    {
                        f"{k}_cell_{bmu}_{cell}": v.value
                        for k, v in bt.get_sensors().items()
                    }
                )
            return result
        except Exception as ex:
            raise UpdateFailed(ex) from ex
        finally:
            await self.pylontech.disconnect()

    async def detect_sensors(self) -> None:
        """Retrieve all supported sensor names from BMS."""
        try:
            await self.pylontech.connect()
            pwr = await self.pylontech.pwr()
            self.sensors = pwr.get_sensors()
            unit = await self.pylontech.unit()
            self.unit_sensors = unit.values[0].get_sensors()
            bat = await self.pylontech.bat()
            self.bat_sensors = bat.values[0].get_sensors()
        finally:
            await self.pylontech.disconnect()

    def sensor_value(self, sensor: str) -> Any:
        """Answer current value of the sensor."""
        return self.data.get(sensor)

    def get_number_of_units(self) -> int:
        """Return  number of units."""
        return len(self._unit_positions)

    def get_unit_number(self, unit_idx: int) -> int:
        """Return stable number of unit with specified serial."""
        return self._unit_positions[unit_idx]


def _device(info: InfoCommand) -> DeviceInfo:
    return DeviceInfo(
        # configuration_url=f"telnet://{pylontech.host}:{pylontech.port}",
        identifiers={(DOMAIN, info.module_barcode.value)},
        name="Pylontech BMS",
        model=info.device_name.value,
        manufacturer=info.manufacturer.value,
        sw_version=f"{info.main_sw_version.value} / {info.sw_version.value}",
        hw_version=info.board_version.value,
        serial_number=info.module_barcode.value,
    )


def _unit_device(info: InfoCommand, idx: int, bmu: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, bmu)},
        name=f"Pylontech BMU #{idx}",
        manufacturer=info.manufacturer.value,
        via_device=(DOMAIN, info.module_barcode.value),
        serial_number=bmu,
    )
