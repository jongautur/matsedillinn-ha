"""Fixtures with the same shape as the server's /api/ha feeds."""

from datetime import date, timedelta

import pytest

from homeassistant.util import dt as dt_util

URL = "https://matsedillinn.net"
TOKEN = "abcdefghijklmnopqrstuvwxyz012345"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


def meal(slot, title, image=None):
    return {
        "slot": slot,
        "slot_label": {"dinner": "Kvöldmatur", "lunch": "Hádegismatur"}.get(slot, slot),
        "title": title,
        "note": None,
        "source": "kronan",
        "minutes": 30,
        "servings": 4,
        "image": image,
        "url": f"{URL}/recipes/1",
    }


def week(offset=0, meals_by_day=None):
    today = dt_util.now().date()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        days.append(
            {
                "date": d.isoformat(),
                "weekday": f"Dagur {i}",
                "weekday_short": f"D{i}",
                "is_today": d == today,
                "meals": (meals_by_day or {}).get(d, []),
            }
        )
    planned = sum(1 for d in days if d["meals"])
    return {
        "week": 1,
        "from": monday.isoformat(),
        "to": (monday + timedelta(days=6)).isoformat(),
        "state": f"{planned}/7",
        "markdown": "\n".join(f"**{d['weekday_short']}** -" for d in days),
        "days": days,
    }


@pytest.fixture
def feeds(aioclient_mock):
    today = dt_util.now().date()
    tomorrow = today + timedelta(days=1)
    meals = {
        today: [meal("lunch", "Skyr"), meal("dinner", "Plokkfiskur", "https://img/p.jpg")],
        tomorrow: [meal("dinner", "Lasagna")],
    }
    this, nxt = week(0, meals), week(1, meals)
    aioclient_mock.get(
        f"{URL}/api/ha/today",
        json={"date": today.isoformat(), "date_label": "í dag", "state": "Plokkfiskur", "meals": meals[today]},
    )
    for offset, data in [(0, this), (1, nxt), (2, week(2)), (-1, week(-1)), (-2, week(-2))]:
        aioclient_mock.get(f"{URL}/api/ha/week?lang=is&offset={offset}", json=data)
    return aioclient_mock
