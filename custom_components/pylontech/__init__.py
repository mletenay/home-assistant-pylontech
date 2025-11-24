"""Support for Pylontech BMS."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN, KEY_COORDINATOR, PLATFORMS
from .coordinator import PylontechUpdateCoordinator
from .pylontech import PylontechBMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Pylontech BMS components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    try:
        _LOGGER.debug("Connecting to Pylontech BMS at %s port %s", host, port)
        pylontech = PylontechBMS(host, port)
        await pylontech.connect()
        info = await pylontech.info()
    except Exception as err:
        raise ConfigEntryNotReady from err
    finally:
        await pylontech.disconnect()

    # Get previously registered devices (to ensure stable order of BMUs)
    device_registry = dr.async_get(hass)
    bmu_serials = tuple(
        sorted(
            {
                device.serial_number
                for device in device_registry.devices.get_devices_for_config_entry_id(
                    entry.entry_id
                )
                if "BMU #" in device.name
            }
        )
    )
    _LOGGER.debug("Loaded existing BMU serials %s", bmu_serials)

    # Create update coordinator
    coordinator = PylontechUpdateCoordinator(
        hass,
        entry,
        pylontech,
        info,
        bmu_serials,
    )
    await coordinator.detect_sensors()

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        KEY_COORDINATOR: coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
