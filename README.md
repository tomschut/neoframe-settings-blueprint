# NeoFrame Settings Server

A Home Assistant **custom integration** that serves the remote settings
JSON a [NeoFrame](https://github.com/tomschut/neoframe) e-paper photo frame
polls for its cron-style wake schedule, timezone, power profile, and
`paused` flag. Home Assistant becomes the single place that schedule and
pause state live, instead of hand-editing JSON on NeoFrame's own
`/schedule` page.

Unlike the [pause/resume blueprint](https://github.com/tomschut/neoframe-pause-automation-blueprint),
which calls NeoFrame's `/pause` and `/resume` endpoints directly (light
sleep, WiFi stays up), this drives NeoFrame's `low_power`/`ac_power`
schedule engine (see the main repo's README, "Scheduled deep sleep")
through the `config_url` it already polls on its own - nothing calls
*into* Home Assistant here, NeoFrame calls *out* to it.

## Why an integration, not a blueprint

This started as a plain automation blueprint using a webhook trigger and
Home Assistant's `stop` + `response_variable` action. That doesn't work:
`response_variable` only answers a **script called via a service call**
with `return_response: true` (e.g. a dashboard button) - a webhook hit
by an external HTTP client (like NeoFrame) always gets an empty `200`
back, no matter what the automation's actions produce. This is a
long-standing, still-open gap in Home Assistant core, not a version quirk
or a blueprint bug. A real HTTP view, which only a custom integration can
register, is the only way to actually return computed content to an
unauthenticated caller.

## Install via HACS

1. HACS → the **⋮** menu → **Custom repositories** → add
   `https://github.com/tomschut/ha-neoframe-settings`, category
   **Integration**.
2. Install **NeoFrame Settings Server**, then restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → NeoFrame Settings
   Server.**

(Or manually: copy `custom_components/neoframe_settings/` into your HA
config's `custom_components/` folder and restart, then add it as above.)

## Configuration

- **Name** - distinguishes multiple frames if you set up more than one.
- **Image URL** - full URL NeoFrame should render, e.g.
  `http://192.168.1.10:8000/frame`.
- **Timezone** - a POSIX TZ rule. `Europe/Amsterdam` and `UTC` are
  recognized as friendly names by NeoFrame; anything else needs the raw
  POSIX rule (e.g. `CET-1CEST,M3.5.0,M10.5.0/3`).
- **Power profile** - `low_power` (deep sleeps between windows, battery
  use), `ac_power` (same schedule, never sleeps, settings page always
  reachable, mains-powered use), or `always_on` (ignores the schedule
  entirely).
- **Schedule** - a JSON array of wake windows, e.g.:
  ```json
  [
    {"days": "mon-fri", "start": "08:00", "stop": "22:00", "every": "5m"},
    {"days": "sat-sun", "start": "10:00", "stop": "23:00", "every": "10m"}
  ]
  ```
- **Paused-when-not source entity** - a `binary_sensor`, `input_boolean`,
  or `group` whose state decides NeoFrame's `paused` flag. You can point
  this at the exact same presence entity the pause/resume blueprint uses.
- **"Active" state** - the state of that entity meaning NeoFrame should be
  active (not paused); anything else pauses it, including the entity being
  missing or unavailable. Default `on`.

All of these can be edited later from the integration entry's **Configure**
button, without removing and re-adding it.

## Point NeoFrame at it

After setup, the integration creates a sensor named "**<name> settings
URL**" whose state is the full URL to paste into NeoFrame's always-on
settings page (`http://<device-ip>/`) as **Settings URL**, e.g.
`http://homeassistant.local:8123/api/neoframe_settings/<entry-id>`. Save
it there and NeoFrame starts polling on its own schedule (or immediately,
via "Force reload now" on that page, or the serial `force` command).

If that sensor's state says to set a Home Assistant URL first: **Settings
→ System → Network**, set an internal URL Home Assistant can reach itself
by (usually already set), then reload this integration's entry.

## What it returns

A `200` JSON response, ETag included, e.g.:

```json
{
  "timezone": "Europe/Amsterdam",
  "power_profile": "low_power",
  "image_url": "http://192.168.1.10:8000/frame",
  "schedule": [
    {"days": "mon-fri", "start": "08:00", "stop": "22:00", "every": "5m"}
  ],
  "paused": false
}
```

The `ETag` is a hash of the exact response body; a request with a matching
`If-None-Match` gets a `304` with no body, matching NeoFrame's conditional
GET support. The `paused` field is computed live from the source entity's
current state on every request - Home Assistant doesn't need to push
anything anywhere.

The view is unauthenticated, matching NeoFrame's own settings-page trust
model (LAN-reachable, no login) - anything already on your network can
read it, same as the settings page itself.
