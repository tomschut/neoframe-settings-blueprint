DOMAIN = "neoframe_settings"

CONF_NAME = "name"
CONF_IMAGE_URL = "image_url"
CONF_TIMEZONE = "timezone"
CONF_POWER_PROFILE = "power_profile"
CONF_SCHEDULE = "schedule"
CONF_PAUSED_ENTITY = "paused_entity"
CONF_ACTIVE_STATE = "active_state"

POWER_PROFILES = ["low_power", "ac_power", "always_on"]

DEFAULT_NAME = "NeoFrame"
DEFAULT_TIMEZONE = "Europe/Amsterdam"
DEFAULT_SCHEDULE = '[{"days": "daily", "start": "08:00", "stop": "22:00", "every": "5m"}]'
DEFAULT_ACTIVE_STATE = "on"

VIEW_URL = "/api/neoframe_settings/{entry_id}"
