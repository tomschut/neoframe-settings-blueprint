from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ACTIVE_STATE,
    CONF_IMAGE_URL,
    CONF_NAME,
    CONF_PAUSED_ENTITY,
    CONF_POWER_PROFILE,
    CONF_SCHEDULE,
    CONF_TIMEZONE,
    DEFAULT_ACTIVE_STATE,
    DEFAULT_NAME,
    DEFAULT_SCHEDULE,
    DEFAULT_TIMEZONE,
    DOMAIN,
    POWER_PROFILES,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_IMAGE_URL, default=defaults.get(CONF_IMAGE_URL, "")): str,
            vol.Required(CONF_TIMEZONE, default=defaults.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)): str,
            vol.Required(
                CONF_POWER_PROFILE, default=defaults.get(CONF_POWER_PROFILE, POWER_PROFILES[0])
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=POWER_PROFILES, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(
                CONF_SCHEDULE, default=defaults.get(CONF_SCHEDULE, DEFAULT_SCHEDULE)
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Required(CONF_PAUSED_ENTITY, default=defaults.get(CONF_PAUSED_ENTITY, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["binary_sensor", "input_boolean", "group"])
            ),
            vol.Required(
                CONF_ACTIVE_STATE, default=defaults.get(CONF_ACTIVE_STATE, DEFAULT_ACTIVE_STATE)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["on", "off"], mode=selector.SelectSelectorMode.DROPDOWN)
            ),
        }
    )


def _validate_schedule(value: str) -> None:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("schedule must be a non-empty JSON array")


class NeoFrameSettingsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                _validate_schedule(user_input[CONF_SCHEDULE])
            except (json.JSONDecodeError, ValueError):
                errors["base"] = "invalid_schedule"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(user_input or {}), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "NeoFrameSettingsOptionsFlow":
        return NeoFrameSettingsOptionsFlow()


class NeoFrameSettingsOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            try:
                _validate_schedule(user_input[CONF_SCHEDULE])
            except (json.JSONDecodeError, ValueError):
                errors["base"] = "invalid_schedule"
            else:
                return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=_schema(current), errors=errors)
