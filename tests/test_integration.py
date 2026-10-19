"""Config flow, sensors and calendar."""

from datetime import timedelta

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.matsedillinn.const import CONF_LANGUAGE, DOMAIN

from .conftest import TOKEN, URL


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="x", data={CONF_URL: URL, CONF_TOKEN: TOKEN, CONF_LANGUAGE: "is"}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_flow_accepts_pasted_link(hass: HomeAssistant, feeds) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "https://ignored", CONF_TOKEN: f"{URL}/calendar.ics?token={TOKEN}", CONF_LANGUAGE: "is"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_URL: URL, CONF_TOKEN: TOKEN, CONF_LANGUAGE: "is"}
    assert feeds.mock_calls[0][3]["Authorization"] == f"Bearer {TOKEN}"


async def test_flow_rejected_key(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{URL}/api/ha/today", status=401)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: URL, CONF_TOKEN: TOKEN, CONF_LANGUAGE: "is"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_sensors(hass: HomeAssistant, feeds) -> None:
    await _setup(hass)
    states = {s.entity_id: s for s in hass.states.async_all("sensor")}
    today = next(s for s in states.values() if s.attributes.get("date_label"))
    assert today.state == "Plokkfiskur"
    assert today.attributes["entity_picture"] == "https://img/p.jpg"
    assert len(today.attributes["meals"]) == 2
    tomorrow = next(s for s in states.values() if "weekday" in s.attributes)
    assert tomorrow.state == "Lasagna"
    week = next(s for s in states.values() if "markdown" in s.attributes)
    assert week.state in ("1/7", "2/7")  # tomorrow may fall in next week


async def test_calendar(hass: HomeAssistant, feeds) -> None:
    await _setup(hass)
    [cal] = hass.states.async_all("calendar")
    assert cal.attributes["message"] == "Plokkfiskur"
    assert cal.attributes["all_day"] is True

    now = dt_util.now()
    resp = await hass.services.async_call(
        "calendar",
        "get_events",
        {"start_date_time": now - timedelta(days=8), "end_date_time": now + timedelta(days=15)},
        target={"entity_id": cal.entity_id},
        blocking=True,
        return_response=True,
    )
    titles = sorted(e["summary"] for e in resp[cal.entity_id]["events"])
    assert titles == ["Lasagna", "Plokkfiskur", "Skyr"]


async def test_rejected_key_starts_reauth(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{URL}/api/ha/today", status=401)
    entry = MockConfigEntry(domain=DOMAIN, unique_id="x", data={CONF_URL: URL, CONF_TOKEN: TOKEN, CONF_LANGUAGE: "is"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == ["reauth"]
