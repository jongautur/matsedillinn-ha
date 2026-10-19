"""The Matseðillinn integration."""

from __future__ import annotations

from homeassistant.const import CONF_TOKEN, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MatsedillinnApi
from .const import CONF_LANGUAGE
from .coordinator import MatsedillinnConfigEntry, MatsedillinnCoordinator

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: MatsedillinnConfigEntry) -> bool:
    api = MatsedillinnApi(
        async_get_clientsession(hass),
        entry.data[CONF_URL],
        entry.data[CONF_TOKEN],
        entry.options.get(CONF_LANGUAGE, entry.data[CONF_LANGUAGE]),
    )
    coordinator = MatsedillinnCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MatsedillinnConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: MatsedillinnConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
