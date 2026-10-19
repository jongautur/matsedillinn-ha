"""Client for the Matseðillinn Home Assistant feeds."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class MatsedillinnError(Exception):
    """The server could not be reached or answered with an error."""


class MatsedillinnAuthError(MatsedillinnError):
    """The key was rejected (it may have been regenerated)."""


class MatsedillinnApi:
    """Reads /api/ha/today and /api/ha/week with a household key."""

    def __init__(self, session: aiohttp.ClientSession, url: str, token: str, language: str) -> None:
        self._session = session
        self._url = url.rstrip("/")
        self._token = token
        self.language = language

    async def today(self) -> dict[str, Any]:
        return await self._get("/api/ha/today")

    async def week(self, offset: int = 0) -> dict[str, Any]:
        return await self._get("/api/ha/week", offset=offset)

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        try:
            async with asyncio.timeout(20):
                resp = await self._session.get(
                    f"{self._url}{path}",
                    params={"lang": self.language, **params},
                    headers={"Authorization": f"Bearer {self._token}"},
                )
                if resp.status == 401:
                    raise MatsedillinnAuthError
                resp.raise_for_status()
                return await resp.json()
        except MatsedillinnError:
            raise
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise MatsedillinnError(str(err)) from err
