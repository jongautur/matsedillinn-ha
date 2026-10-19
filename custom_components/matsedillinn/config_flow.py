"""Config flow: paste one of the links from Stillingar → Ytri tengingar, or just the key."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from typing import Any
from urllib.parse import parse_qs, urlsplit

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_TOKEN, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .api import MatsedillinnApi, MatsedillinnAuthError, MatsedillinnError
from .const import CONF_LANGUAGE, DEFAULT_URL, DOMAIN, LANGUAGES
from .coordinator import MatsedillinnConfigEntry

LANGUAGE_SELECTOR = SelectSelector(
    SelectSelectorConfig(options=LANGUAGES, mode=SelectSelectorMode.DROPDOWN, translation_key="language")
)


def _split_link(url: str, token: str) -> tuple[str, str]:
    """A pasted feed link gives both the server and the key."""
    token = token.strip()
    parts = urlsplit(token)
    if parts.scheme in ("http", "https") and parts.netloc:
        key = parse_qs(parts.query).get("token", [""])[0]
        return f"{parts.scheme}://{parts.netloc}", key
    return url.strip().rstrip("/"), token


def _unique_id(token: str) -> str:
    # One entry per household key, without storing the key in the registry id.
    return hashlib.sha256(token.encode()).hexdigest()[:16]


class MatsedillinnConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, url: str, token: str, language: str) -> str | None:
        if len(token) < 16:
            return "invalid_auth"
        api = MatsedillinnApi(async_get_clientsession(self.hass), url, token, language)
        try:
            await api.today()
        except MatsedillinnAuthError:
            return "invalid_auth"
        except MatsedillinnError:
            return "cannot_connect"
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        language = self.hass.config.language.split("-")[0]
        if language not in LANGUAGES:
            language = "en"

        if user_input is not None:
            url, token = _split_link(user_input[CONF_URL], user_input[CONF_TOKEN])
            language = user_input[CONF_LANGUAGE]
            if not (error := await self._validate(url, token, language)):
                await self.async_set_unique_id(_unique_id(token))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Matseðillinn",
                    data={CONF_URL: url, CONF_TOKEN: token, CONF_LANGUAGE: language},
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=DEFAULT_URL): str,
                    vol.Required(CONF_TOKEN): str,
                    vol.Required(CONF_LANGUAGE, default=language): LANGUAGE_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            url, token = _split_link(entry.data[CONF_URL], user_input[CONF_TOKEN])
            if not (error := await self._validate(url, token, entry.data[CONF_LANGUAGE])):
                # Regenerating the key changes the unique id along with it.
                return self.async_update_reload_and_abort(
                    entry, unique_id=_unique_id(token), data_updates={CONF_URL: url, CONF_TOKEN: token}
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: MatsedillinnConfigEntry) -> OptionsFlow:
        return MatsedillinnOptionsFlow()


class MatsedillinnOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_LANGUAGE, self.config_entry.data[CONF_LANGUAGE])
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required(CONF_LANGUAGE, default=current): LANGUAGE_SELECTOR}),
        )
