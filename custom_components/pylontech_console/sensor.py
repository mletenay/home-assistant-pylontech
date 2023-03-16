"""Pylontech (high voltage) BMS sensors."""
from __future__ import annotations

from .const import DOMAIN, KEY_COORDINATOR
from .coordinator import PylontechUpdateCoordinator

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity


_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "A": SensorEntityDescription(
        key="A",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    "V": SensorEntityDescription(
        key="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    "Ah": SensorEntityDescription(
        key="Ah",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    "Wh": SensorEntityDescription(
        key="Wh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
    ),
    "C": SensorEntityDescription(
        key="C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    "%": SensorEntityDescription(
        key="%",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    " ": SensorEntityDescription(
        key="text",
    ),
}
DIAG_SENSOR = SensorEntityDescription(
    key="_",
    state_class=SensorStateClass.MEASUREMENT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities from a config entry."""
    coordinator: PylontechUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        KEY_COORDINATOR
    ]

    # Individual inverter sensors entities
    entities: list[PylontectSensorEntity] = []
    entities.extend(
        PylontectSensorEntity(coordinator, id, sensor.name, sensor.unit)
        for id, sensor in coordinator.sensors.items()
    )

    async_add_entities(entities)


class PylontectSensorEntity(
    CoordinatorEntity[PylontechUpdateCoordinator], SensorEntity
):
    """Representation of an Electric Vehicle Charger status device."""

    def __init__(
        self,
        coordinator: PylontechUpdateCoordinator,
        sensor: str,
        name: str,
        unit: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{sensor}-{coordinator.serial_nr}"
        self._attr_device_info = coordinator.device_info
        self.entity_description = _DESCRIPTIONS.get(unit, DIAG_SENSOR)
        self._sensor = sensor

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return self.coordinator.sensor_value(self._sensor)
