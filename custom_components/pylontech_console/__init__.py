"""Support for Pylontech (high voltage) BMS accessed via console."""
import logging

from .const import (
    DOMAIN,
    KEY_COORDINATOR,
    PLATFORMS,
)
from .coordinator import PylontechUpdateCoordinator
from .pylontech import PylontechConsole

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.sensor import PLATFORM_SCHEMA

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Pylontech BMS components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    try:
        _LOGGER.debug("Connecting to Pylontech BMS at %s port %s", host, port)
        pylontech = PylontechConsole(host, port)
        await pylontech.connect()
        info = await pylontech.info()
        await pylontech.disconnect()
    except Exception as err:
        raise ConfigEntryNotReady from err

    # Create update coordinator
    coordinator = PylontechUpdateCoordinator(hass, entry, pylontech, info)
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
