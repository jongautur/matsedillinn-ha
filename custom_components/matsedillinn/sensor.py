"""Sensors for today's and tomorrow's meals and the week's plan."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import NOTHING_PLANNED
from .coordinator import MatsedillinnConfigEntry, MatsedillinnCoordinator, MatsedillinnData
from .entity import MatsedillinnEntity


def _main_meal(meals: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Dinner if planned, otherwise the first meal of the day."""
    return next((m for m in meals if m["slot"] == "dinner"), meals[0] if meals else None)


def _tomorrow(data: MatsedillinnData) -> dict[str, Any] | None:
    days = data.days()
    i = next((i for i, d in enumerate(days) if d["is_today"]), None)
    return days[i + 1] if i is not None and i + 1 < len(days) else None


@dataclass(frozen=True, kw_only=True)
class MatsedillinnSensorDescription(SensorEntityDescription):
    value: Callable[[MatsedillinnData, str], str]
    attributes: Callable[[MatsedillinnData], dict[str, Any]]
    meals: Callable[[MatsedillinnData], list[dict[str, Any]]] = lambda _: []


def _tomorrow_value(data: MatsedillinnData, language: str) -> str:
    meal = _main_meal((_tomorrow(data) or {}).get("meals", []))
    return meal["title"] if meal else NOTHING_PLANNED[language]


SENSORS = (
    MatsedillinnSensorDescription(
        key="today",
        icon="mdi:silverware-fork-knife",
        value=lambda data, _: data.today["state"],
        attributes=lambda data: {
            "date": data.today["date"],
            "date_label": data.today["date_label"],
            "meals": data.today["meals"],
        },
        meals=lambda data: data.today["meals"],
    ),
    MatsedillinnSensorDescription(
        key="tomorrow",
        icon="mdi:silverware-fork-knife",
        value=_tomorrow_value,
        attributes=lambda data: {
            "date": (day := _tomorrow(data) or {}).get("date"),
            "weekday": day.get("weekday"),
            "meals": day.get("meals", []),
        },
        meals=lambda data: (_tomorrow(data) or {}).get("meals", []),
    ),
    MatsedillinnSensorDescription(
        key="week",
        icon="mdi:calendar-week",
        value=lambda data, _: data.week["state"],
        attributes=lambda data: {
            "week": data.week["week"],
            "from": data.week["from"],
            "to": data.week["to"],
            "markdown": data.week["markdown"],
            "days": data.week["days"],
            "next_week_markdown": data.next_week["markdown"],
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: MatsedillinnConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(MatsedillinnSensor(entry.runtime_data, d) for d in SENSORS)


class MatsedillinnSensor(MatsedillinnEntity, SensorEntity):
    entity_description: MatsedillinnSensorDescription

    def __init__(self, coordinator: MatsedillinnCoordinator, description: MatsedillinnSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str:
        return self.entity_description.value(self.coordinator.data, self.coordinator.api.language)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.entity_description.attributes(self.coordinator.data)

    @property
    def entity_picture(self) -> str | None:
        meal = _main_meal(self.entity_description.meals(self.coordinator.data))
        return meal["image"] if meal else None
