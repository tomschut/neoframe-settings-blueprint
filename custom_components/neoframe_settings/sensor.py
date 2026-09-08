from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import DOMAIN, VIEW_URL


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([NeoFrameSettingsUrlSensor(hass, entry)])


class NeoFrameSettingsUrlSensor(SensorEntity):
    """Shows the full webhook-style URL to paste into NeoFrame's Settings URL field."""

    _attr_icon = "mdi:link-variant"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._attr_unique_id = f"{entry.entry_id}_url"
        self._attr_name = f"{entry.title} settings URL"
        path = VIEW_URL.format(entry_id=entry.entry_id)
        try:
            base = get_url(hass, prefer_external=False, allow_internal=True, allow_ip=True)
        except NoURLAvailableError:
            self._attr_native_value = f"Set a Home Assistant URL, then reload this entry ({path})"
        else:
            self._attr_native_value = f"{base}{path}"
