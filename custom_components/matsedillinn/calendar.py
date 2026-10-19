"""The meal plan as a calendar, one all-day event per meal."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import MatsedillinnError
from .const import MAX_WEEK_OFFSET, MIN_WEEK_OFFSET
from .coordinator import MatsedillinnConfigEntry, MatsedillinnCoordinator
from .entity import MatsedillinnEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: MatsedillinnConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([MatsedillinnCalendar(entry.runtime_data)])


def _events(days: list[dict[str, Any]]) -> list[CalendarEvent]:
    events = []
    for day in days:
        start = date.fromisoformat(day["date"])
        for meal in day["meals"]:
            description = "\n".join(filter(None, [meal["slot_label"], meal["note"], meal["url"]]))
            events.append(
                CalendarEvent(
                    start=start,
                    end=start + timedelta(days=1),
                    summary=meal["title"],
                    description=description or None,
                    uid=f"{day['date']}-{meal['slot']}",
                )
            )
    return events


class MatsedillinnCalendar(MatsedillinnEntity, CalendarEntity):
    def __init__(self, coordinator: MatsedillinnCoordinator) -> None:
        super().__init__(coordinator, "plan")

    @property
    def event(self) -> CalendarEvent | None:
        """Today's dinner (or first meal), else the next planned meal."""
        today = dt_util.now().date()
        upcoming = [e for e in _events(self.coordinator.data.days()) if e.start >= today]
        todays = [e for e in upcoming if e.start == today]
        dinner = next((e for e in todays if e.uid and e.uid.endswith("-dinner")), None)
        return dinner or (upcoming[0] if upcoming else None)

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        data = self.coordinator.data
        monday = date.fromisoformat(data.week["from"])
        first = max(MIN_WEEK_OFFSET, (start_date.date() - monday).days // 7)
        last = min(MAX_WEEK_OFFSET, (end_date.date() - monday).days // 7)

        days: list[dict[str, Any]] = []
        for offset in range(first, last + 1):
            if offset == 0:
                days += data.week["days"]
            elif offset == 1:
                days += data.next_week["days"]
            else:
                try:
                    days += (await self.coordinator.api.week(offset))["days"]
                except MatsedillinnError as err:
                    raise HomeAssistantError(f"Could not fetch week {offset}: {err}") from err

        return [e for e in _events(days) if e.end > start_date.date() and e.start < end_date.date()]
