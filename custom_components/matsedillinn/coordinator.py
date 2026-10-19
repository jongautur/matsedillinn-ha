"""Polls today's meals and this and next week's plan."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MatsedillinnApi, MatsedillinnAuthError, MatsedillinnError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type MatsedillinnConfigEntry = ConfigEntry[MatsedillinnCoordinator]


@dataclass
class MatsedillinnData:
    today: dict[str, Any]
    week: dict[str, Any]
    next_week: dict[str, Any]

    def days(self) -> list[dict[str, Any]]:
        """This week's and next week's days, in order."""
        return self.week["days"] + self.next_week["days"]


class MatsedillinnCoordinator(DataUpdateCoordinator[MatsedillinnData]):
    config_entry: MatsedillinnConfigEntry

    def __init__(self, hass: HomeAssistant, entry: MatsedillinnConfigEntry, api: MatsedillinnApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> MatsedillinnData:
        try:
            return MatsedillinnData(
                today=await self.api.today(),
                week=await self.api.week(0),
                next_week=await self.api.week(1),
            )
        except MatsedillinnAuthError as err:
            raise ConfigEntryAuthFailed("The key was rejected") from err
        except MatsedillinnError as err:
            raise UpdateFailed(str(err)) from err
