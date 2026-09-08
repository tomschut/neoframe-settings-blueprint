"""NeoFrame Settings Server: serves NeoFrame's config_url JSON from Home Assistant.

Plain HA automations/blueprints can't do this - a webhook trigger has no way
to return a computed response body to the caller (stop/response_variable
only answers a script called via a service call with return_response, never
an incoming HTTP request). This registers a real, unauthenticated HTTP view
instead, since that's the only way that actually works on stock HA.
"""
from __future__ import annotations

import hashlib
import json
import logging

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ACTIVE_STATE,
    CONF_IMAGE_URL,
    CONF_PAUSED_ENTITY,
    CONF_POWER_PROFILE,
    CONF_SCHEDULE,
    CONF_TIMEZONE,
    DOMAIN,
    VIEW_URL,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


class NeoFrameSettingsView(HomeAssistantView):
    """Serves one NeoFrame device's settings JSON at VIEW_URL, keyed by entry_id."""

    url = VIEW_URL
    name = "api:neoframe_settings"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str) -> web.Response:
        entries = self.hass.data.get(DOMAIN, {}).get("entries", {})
        entry: ConfigEntry | None = entries.get(entry_id)
        if entry is None:
            return web.Response(status=404, text="Unknown NeoFrame settings endpoint")

        options = {**entry.data, **entry.options}

        state = self.hass.states.get(options[CONF_PAUSED_ENTITY])
        paused = True if state is None else state.state != options[CONF_ACTIVE_STATE]

        try:
            schedule = json.loads(options[CONF_SCHEDULE])
        except (TypeError, ValueError):
            _LOGGER.warning("Stored schedule for %s is not valid JSON; serving empty schedule", entry.title)
            schedule = []

        payload = {
            "timezone": options[CONF_TIMEZONE],
            "power_profile": options[CONF_POWER_PROFILE],
            "image_url": options[CONF_IMAGE_URL],
            "schedule": schedule,
            "paused": paused,
        }
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        etag = hashlib.sha256(body.encode()).hexdigest()

        if request.headers.get("If-None-Match") == etag:
            return web.Response(status=304, headers={"ETag": etag})

        return web.Response(text=body, status=200, content_type="application/json", headers={"ETag": etag})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {"entries": {}, "view_registered": False})
    if not domain_data["view_registered"]:
        hass.http.register_view(NeoFrameSettingsView(hass))
        domain_data["view_registered"] = True
    domain_data["entries"][entry.entry_id] = entry

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    return unload_ok
